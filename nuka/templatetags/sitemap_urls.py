# coding=utf-8
from __future__ import unicode_literals
from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from account.models import User

register = template.Library()

sitemap_items = [
    {
        'url': 'frontpage',
        'name': _('Etusivu'),
        'sub': False
    },
    {
        'url': 'account:signup_choices',
        'name': _('Rekisteröidy'),
        'sub': False
    },
    {
        'url': 'account:login',
        'name': _('Kirjaudu'),
        'sub': False
    },
    {
        'url': 'content:initiative_list',
        'name': _('Ideat'),
        'sub': False
    },
    {
        'url': 'content:create_idea',
        'name': _('Kirjoita idea'),
        'sub': True
    },
    {
        'url': 'organization:list',
        'name': _('Organisaatiot'),
        'sub': False
    },
    {
        'url': 'organization:create',
        'name': _('Luo organisaatio'),
        'sub': True
    },
    {
        'url': 'help:instruction_list',
        'name': _('Tietoa palvelusta'),
        'sub': False
    },
    {
        'url': 'help:linked_instruction_redirect',
        'name': _('Tietosuojaseloste'),
        'slug': 'privacy-policy',
        'sub': True
    },
    {
        'url': 'help:linked_instruction_redirect',
        'name': _('Saavutettavuusseloste'),
        'slug': 'accessibility-statement',
        'sub': True
    },
    {
        'url': 'help:linked_instruction_redirect',
        'name': _('Yhteystiedot'),
        'slug': 'contact-details',
        'sub': True
    },
    {
        'url': 'campaign:campaign_list',
        'name': _('Materiaalit'),
        'sub': False
    },
    {
        'url': 'info:topic_list',
        'name': _("Ajankohtaista"),
        'sub': False,
    },
    {
        'url': 'feedback',
        'name': _('Palaute'),
        'sub': False
    },
]

# URLs that require authentication
secure_sitemap_items = [
    {
        'url': 'account:profile',
        'name': _('Oma sivu'),
        'user_only': True,
        'sub': False
    },
    {
        'url': 'nkadmin:moderation_queue',
        'name': _('Hallinta'),
        'moderator_only': True,
        'sub': False
    }
]


def secure_urls(user):
    current_user = User.objects.get(pk=user)
    items = []
    for item in secure_sitemap_items:
        if 'user_only' in item and current_user.is_authenticated:
            items.append({'url': reverse(item['url'], kwargs={'user_id': user}),
                          'name': item['name'],
                          'sub': item['sub']})
        elif 'moderator_only' in item and current_user.is_moderator:
            items.append({'url': reverse(item['url']),
                          'name': item['name'],
                          'sub': item['sub']})
    return items


@register.inclusion_tag('nuka/sitemap_items.html')
def all_urls(user):
    items = []
    for item in sitemap_items:
        if 'slug' in item:
            items.append({'url': reverse(item['url'], kwargs={'slug': item['slug']}),
                          'name': item['name'],
                          'sub': item['sub']})
        else:
            items.append({'url': reverse(item['url']),
                          'name': item['name'],
                          'sub': item['sub']})
    if user:
        items += secure_urls(user)
    return {'sitemap_items': items}
