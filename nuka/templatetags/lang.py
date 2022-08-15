# coding=utf-8

from __future__ import unicode_literals

from operator import itemgetter
import re

from django import template
from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from django.template.loader import render_to_string
from django.utils.translation import override, get_language, activate

register = template.Library()

lang_prefix = re.compile(r'^\/(%s)\/' % '|'.join(map(itemgetter(0), settings.LANGUAGES)))


@register.simple_tag(takes_context=True)
def lang_switch(context, lang=None):
    cur_language = get_language()
    path = lang_prefix.sub('/', context['request'].path)
    path = "/{}{}".format(cur_language, path)
    url_parts = resolve(path)
    url = path  # todo: is this necessary?

    try:
        activate(lang)
        url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        activate(cur_language)

    return "%s" % url


@register.simple_tag(takes_context=True)
def include_translated(context, template_name, lang):
    with override(lang):
        html = render_to_string(template_name, context)
    return html
