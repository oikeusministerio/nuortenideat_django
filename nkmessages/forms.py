# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from nocaptcha_recaptcha import NoReCaptchaField

from nuka.utils import strip_tags, strip_emojis
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    message = forms.CharField(label=_('Viesti'), widget=forms.Textarea)
    captcha = NoReCaptchaField(
        label=_('Tarkistuskoodi'),
        error_messages={'invalid': _('Virheellinen tarkistuskoodi.')}
    )

    def __init__(self, user=None, *args, **kwargs):
        super(FeedbackForm, self).__init__(*args, **kwargs)
        if user:
            del self.fields["name"]
            del self.fields["email"]
            del self.fields["captcha"]

    def clean_message(self):
        message = strip_tags(self.cleaned_data["message"])
        cleaned_message = strip_emojis(message)
        if cleaned_message == "" or cleaned_message.isspace():
            raise forms.ValidationError(_('Tämä kenttä ei voi olla tyhjä.'))
        return cleaned_message

    def clean_subject(self):
        subject = strip_tags(self.cleaned_data["subject"])
        cleaned_subject = strip_emojis(subject)
        if cleaned_subject == "" or cleaned_subject.isspace():
            raise forms.ValidationError(_('Tämä kenttä ei voi olla tyhjä.'))
        return cleaned_subject

    class Meta:
        model = Feedback
        fields = ("name", "email", "subject", "message")
