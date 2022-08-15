# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext

from import_export import resources, fields

from content.models import Idea
from .models import Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )


admin.site.register(Tag, TagAdmin)


class TagResource(resources.ModelResource):
    name = fields.Field(column_name=ugettext("Aihe"))
    count_ideas = fields.Field(column_name=ugettext("Esiintyy (kpl) ideassa"))

    def dehydrate_name(self, tag):
        return tag

    def dehydrate_count_ideas(self, tag):
        ct = ContentType.objects.get_for_model(Idea)
        return tag.initiative_set.filter(polymorphic_ctype_id=ct.pk).count()

    class Meta:
        model = Tag
        fields = ('name', 'count_ideas')
        export_order = ('name', 'count_ideas')
