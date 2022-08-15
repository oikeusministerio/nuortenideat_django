# coding=utf-8

from __future__ import unicode_literals
from functools import wraps

from uuid import uuid4
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from account.models import UserSettings


def _carousel_pic_path(size):
    @wraps(_carousel_pic_path)
    def inner(obj, name):
        return 'carousel/%d/%s_%s_%s.jpg' % (
            obj.carousel_set.pk, obj.language, size, uuid4().hex
        )
    return inner


class CarouselImageField(models.ImageField):
    def __init__(self, *args, **kwargs):
        self.width = kwargs.pop("width")
        self.height = kwargs.pop("height")
        self.upload_to_size = kwargs.pop("upload_to_size")
        kwargs["upload_to"] = _carousel_pic_path(self.upload_to_size)
        super(CarouselImageField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CarouselImageField, self).deconstruct()
        kwargs["width"] = self.width
        kwargs["height"] = self.height
        kwargs["upload_to_size"] = self.upload_to_size
        del kwargs["upload_to"]
        return name, path, args, kwargs

    def clean(self, value, model_instance):
        if self.width != value.width or self.height != value.height:
            # raise ValidationError(_("Kuvan korkeus tai leveys ei vastaa pyydettyä."))
            pass
        return value


@python_2_unicode_compatible
class PictureCarouselSet(models.Model):
    name = models.CharField(_("Nimi"), max_length=100)
    is_active = models.BooleanField(_("aktiivinen"), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("kuvakarusellin kuva")
        verbose_name_plural = _("kuvakarusellin kuvat")


@python_2_unicode_compatible
class PictureCarouselImage(models.Model):
    carousel_set = models.ForeignKey(PictureCarouselSet, related_name="images")

    language = models.CharField(
        _("kieli"), choices=UserSettings.LANGUAGE_CHOICES,
        max_length=5, default=UserSettings.LANGUAGE_CHOICES[0][0],
        help_text=_("Lisää kuvat vain kerran per kieli.")
    )

    def validate_image(image):
        max_width = 1920
        min_width = 1000
        max_height = 800
        min_height = 500
        width, height = get_image_dimensions(image.file)
        if width > max_width or height > max_height:
            raise ValidationError("Kuvan korkeus tai leveys on liian suuri.")
        elif width < min_width or height < min_height:
            raise ValidationError("Kuvan korkeus tai leveys on liian pieni.")

    original = models.ImageField(
        _("kuva"), upload_to=_carousel_pic_path("original"), null=True,
        validators=[validate_image],
        help_text="Sallittu leveys: 1000px - 1920px, sallittu korkeus: 500px - 800px"
    )

    alt_text = models.CharField(_("alt-teksti"), max_length=255)

    def __str__(self):
        choices = UserSettings.LANGUAGE_CHOICES
        value = next((v for k, v in choices if k == self.language), None)
        return value.encode("utf-8").capitalize()

    class Meta:
        unique_together = ("carousel_set", "language")
        verbose_name = _("kuvan kieliversio")
        verbose_name_plural = _("kuvan kieliversiot")
