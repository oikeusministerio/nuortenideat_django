# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django_comments.forms import CommentForm
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from nocaptcha_recaptcha import NoReCaptchaField
from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn
from nkcomments.models import CustomComment

from nuka.forms.fields import SaferRedactorField
from nuka.utils import strip_tags, strip_emojis
from nuka.forms.forms import StripEmojisMixin


class BaseCustomCommentForm(StripEmojisMixin, CommentForm):
    honeypot = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
        label=_("If you enter anything in this field your comment "
                "will be treated as spam")
    )
    name = forms.CharField(label=_("Nimi"), max_length=50)

    def get_comment_create_data(self):
        return dict(
            content_type=ContentType.objects.get_for_model(self.target_object),
            object_pk=force_text(self.target_object._get_pk_val()),
            user_name=self.cleaned_data['name'],
            comment=self.clean_comment(),
            submit_date=timezone.now(),
            site_id=settings.SITE_ID,
            is_public=True,
            is_removed=False,
        )

    def clean_comment(self):
        comment = strip_tags(self.cleaned_data["comment"])
        cleaned_comment = strip_emojis(comment)
        if cleaned_comment == "" or cleaned_comment.isspace():
            raise forms.ValidationError(_('Tämä kenttä ei voi olla tyhjä.'))
        return cleaned_comment

    def get_comment_model(self):
        return CustomComment


class CustomCommentFormAnon(BaseCustomCommentForm):
    captcha = NoReCaptchaField(
        label=_("Tarkistuskoodi"),
        error_messages={'invalid': _("Virheellinen tarkistuskoodi.")},
    )
    strip_emoji_fields = ['comment', 'name']


class CustomCommentForm(RedactorAttachtorFormMixIn, BaseCustomCommentForm):
    name = forms.CharField(widget=forms.HiddenInput, required=False, label=_("Nimi"))
    comment = SaferRedactorField(allow_file_upload=True, allow_image_upload=True,
                                 label=_("Kommentti"))
    strip_emoji_fields = ['comment']


class BaseCommentEditForm(StripEmojisMixin, forms.ModelForm):
    strip_emoji_fields = ['comment']

    def clean_comment(self):
        comment = strip_tags(self.cleaned_data["comment"])
        cleaned_comment = strip_emojis(comment)
        if cleaned_comment.isspace():
            return ""
        return cleaned_comment

    class Meta:
        model = CustomComment
        fields = ('comment', )


class CommentEditForm(RedactorAttachtorFormMixIn, BaseCommentEditForm):
    comment = SaferRedactorField(allow_file_upload=True, allow_image_upload=True,
                                 label=_("Kommentti"))

    def clean_comment(self):
        comment = strip_tags(self.cleaned_data["comment"])
        cleaned_comment = strip_emojis(comment)
        if cleaned_comment.isspace():
            raise forms.ValidationError(_('Tämä kenttä ei voi olla tyhjä.'))
        return cleaned_comment

    class Meta:
        model = CustomComment
        fields = ('comment', )


class AnonCommentEditForm(BaseCommentEditForm):
    comment = forms.CharField(widget=forms.Textarea, label=_("Kommentti"))


CustomCommentFormAnon.base_fields.pop('email')
CustomCommentFormAnon.base_fields.pop('url')
CustomCommentForm.base_fields.pop('email')
CustomCommentForm.base_fields.pop('url')



