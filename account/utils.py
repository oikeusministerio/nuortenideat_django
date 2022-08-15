# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate
from django.core.urlresolvers import reverse

from nuka.utils import send_email
from .models import ClientIdentifier, User, GROUP_NAME_MODERATORS


def get_client_identifier(request):
    ci, _new = ClientIdentifier.objects.get_or_create(
        ip=request.META["REMOTE_ADDR"],
        user_agent=request.META.get("HTTP_USER_AGENT", '-')
    )
    return ci


def remove_archived_users_emails(email_list):
    archived_emails = User.objects.filter(
        settings__email__in=email_list, status=User.STATUS_ARCHIVED).\
        values_list('settings__email', flat=True)

    if not len(archived_emails):
        return email_list
    return [email for email in email_list if email not in archived_emails]


def send_moderator_rights_reminder_email(reminding_days):
    activate(settings.LANGUAGE_CODE)
    remind_date = date.today() + timedelta(days=reminding_days)
    users = User.objects.filter(
        groups__name=GROUP_NAME_MODERATORS,
        moderator_rights_valid_until=remind_date
    )
    link = settings.BASE_URL + reverse('nkadmin:moderator_rights')
    for user in users:
        send_email(
            _("Varoitus moderointioikeuksien vanhentumisesta."),
            "account/email/remind_moderator_rights.txt",
            {
                "username": user.username,
                "days_left": reminding_days,
                "link": link,
            },
            [user.settings.email, ],
        )
    return users
