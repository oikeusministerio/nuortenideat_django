# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from django.db.models import TextField

from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn
from libs.multilingo.forms.widgets import MultiLingualWidget

from .models import Organization


class OrganizationAdminForm(RedactorAttachtorFormMixIn, forms.ModelForm):

    class Media:
        js = {
            "redactor/langs/fi.js",
            "redactor/langs/sv.js"
        }


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationAdminForm
    list_display = ('name', 'type', 'is_active')
    exclude = ('original_picture', 'picture', 'cropping')

    # TODO: HACK!
    formfield_overrides = {
        TextField: {'widget': MultiLingualWidget}
    }

