# coding=utf-8

from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.conf import settings
from account.pipeline import BACKEND_KEY_FB, BACKEND_KEY_GOOGLE, BACKEND_KEY_INSTAGRAM


def nuka_settings(req):
    site_name = _('Nuortenideat.fi')
    if settings.PRACTICE:
        site_name = _('Nuortenideat.fi harjoittelu')

    return {
        'BASE_URL': settings.BASE_URL,
        'PRACTICE': settings.PRACTICE,
        'SITE_NAME': site_name,
        'ABSOLUTE_URI': req.build_absolute_uri(),
        'BACKEND_KEY_FB': BACKEND_KEY_FB,
        'BACKEND_KEY_GOOGLE': BACKEND_KEY_GOOGLE,
        'BACKEND_KEY_INSTAGRAM': BACKEND_KEY_INSTAGRAM,
        'MATOMO_ID': getattr(settings, 'MATOMO_ID', None),
        'MATOMO_URL': getattr(settings, 'MATOMO_URL', None),
    }
