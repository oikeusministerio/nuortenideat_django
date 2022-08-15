# coding=utf-8

from __future__ import unicode_literals

from operator import attrgetter

from django import template

from nuka.utils import chunks
from tagging.utils import tags_by_popularity


register = template.Library()


@register.assignment_tag
def popular_tags():
    tags = tags_by_popularity()[:8]
    sizes = ('large', 'medium', 'small')
    for i, tag_group in enumerate(chunks(tags, 3)):
        for tag in tag_group:
            tag.size = sizes[i]
    return sorted(tags, key=attrgetter("name"))
