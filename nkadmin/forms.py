# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms.models import ModelChoiceField
from django.utils import timezone
from django.utils.translation import ugettext as _

from bootstrap3_datetime.widgets import DateTimePicker
from account.forms import CustomPhoneNumberField
from libs.fimunicipality.models import Municipality
from datetime import timedelta

from nuka.forms.fields import ModelMultipleChoiceField
from nuka.forms.widgets import Select2
from account.models import User, UserSettings, GROUP_LABELS
from nuka.utils import send_email
from organization.models import Organization


class GroupChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return dict(GROUP_LABELS).get(obj.name, obj.name)


class UserSearchForm(forms.ModelForm):
    organizations = ModelMultipleChoiceField(queryset=Organization.objects.all().
                                             order_by('name'),
                                             label=_("Rajaa organisaatiolla"),
                                             required=False)

    def form_filter(self, qs):
        organizations = self.cleaned_data['organizations']
        if organizations:
            qs = qs.filter(organizations__pk__in=organizations)
        return qs

    class Meta:
        model = User
        fields = ('organizations', )


class EditUserForm(forms.ModelForm):
    username = forms.CharField(label=_("Käyttäjänimi"), min_length=3, max_length=30)
    groups = GroupChoiceField(label=_("Käyttäjäryhmät"), queryset=Group.objects.all(),
                              required=False, help_text="")
    organizations = ModelMultipleChoiceField(queryset=Organization.objects.all(),
                                             label=_("Organisaatiot"), required=False)

    def __init__(self, *args, **kwargs):
        self.target_user = User.objects.get(pk=kwargs.pop("target_user"))
        is_admin = kwargs.pop("editor_is_admin")
        super(EditUserForm, self).__init__(*args, **kwargs)
        if not is_admin:
            del self.fields["groups"]

    def save(self, commit=True):
        changed = self.has_changed() and "groups" in self.changed_data
        super(EditUserForm, self).save(commit)
        if changed:
            self.update_moderator_rights_length()
            send_email(
                _("Käyttöoikeuksiisi tehtiin muutoksia"),
                "nkadmin/email/group_change.txt",
                {"target_user": self.target_user},
                [self.target_user.settings.email],
                self.target_user.settings.language
            )

    def update_moderator_rights_length(self):
        user = self.target_user
        is_moderator = _("Moderaattori") in user.get_groups_joined()
        if is_moderator:
            now = timezone.now().date()
            moderator_rights_default_length = timedelta(
                days=settings.MODERATOR_RIGHTS_VALID_DAYS)
            moderator_rights_end_date = now + moderator_rights_default_length
            user.moderator_rights_valid_until = moderator_rights_end_date
            user.save()
        else:
            user.moderator_rights_valid_until = None
            user.save()

    class Meta:
        model = User
        fields = ("username", "status", "groups", "organizations")


class EditUserSettingsForm(forms.ModelForm):
    municipality = forms.ModelChoiceField(label=_("Kotikunta"),
                                          queryset=Municipality.objects.all(),
                                          widget=Select2, required=True,
                                          empty_label=_("Valitse"))
    phone_number = CustomPhoneNumberField(required=False)

    """
    def clean_email(self):
        username = self.cleaned_data.get('email', None)
        if username:
            if bool(self._meta.model._default_manager.filter(email=username)):
                raise forms.ValidationError(_("Sähköpostiosoite on jo käytössä."))
        return username
    """

    class Meta:
        model = UserSettings
        fields = ("first_name", "last_name", "birth_year", "municipality",
                  "email", "phone_number", "message_notification")


class UpdateModeratorRightsForm(forms.Form):
    pass
