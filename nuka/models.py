# coding=utf-8

from __future__ import unicode_literals

from libs.attachtor.models.fields import RedactorAttachtorFieldMixIn

from libs.multilingo.models import fields as multilingo

from .forms import fields as forms
from .forms.widgets import MultiLingualWidget

from django.db import models


class MySQLDatetimeDate(models.Transform):
    """
    This implements a custom SQL lookup when using `__date` with datetimes.
    To enable filtering on datetimes that fall on a given date, import
    this transform and register it with the DateTimeField.
    """
    lookup_name = 'date'

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return 'DATE({})'.format(lhs), params

    @property
    def output_field(self):
        return models.DateField()


models.DateTimeField.register_lookup(MySQLDatetimeDate)


class MultilingualTextField(multilingo.MultilingualTextField):
    def formfield(self, **kwargs):
        kwargs.setdefault('widget', MultiLingualWidget)
        return super(MultilingualTextField, self).formfield(**kwargs)


class MultilingualRedactorField(RedactorAttachtorFieldMixIn,
                                multilingo.MultilingualTextField):
    description = "Multilingual text field with RedactorAttachtorWidget"

    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', forms.MultilingualRedactorField)
        kwargs.setdefault('widget', MultiLingualWidget)
        return super(MultilingualRedactorField, self).formfield(**kwargs)

    def extract_html_from_field(self, instance, field_name):
        v = getattr(instance, field_name)
        # v is a dictionary, with language codes as keys, html for that language as value
        html = ''.join(v.values())
        return html
