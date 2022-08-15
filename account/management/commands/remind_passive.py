# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils.translation import activate, ugettext_lazy as _

from account.models import User
from nuka.utils import send_email


class Command(BaseCommand):
    help = 'Reminds users that have been passive for %s days' % \
           settings.REMOVE_PASSIVE_USERS_REMINDING_DAYS

    def remind_users(self, last_login, reminding_days):
        users = User.objects.filter(
            Q(last_login__startswith=last_login) |
            Q(last_login__isnull=True,
              joined__startswith=last_login,
              status=User.STATUS_ACTIVE)
        )
        count = users.count()
        activate(settings.LANGUAGE_CODE)

        days_until = settings.REMOVE_PASSIVE_USERS_DAYS - reminding_days

        for user in users:
            send_email(
                _("Varoitus käyttäjätilin poistamisesta."),
                "account/email/remind_passive_users.txt",
                {
                    "username": user.username,
                    "days_until": days_until,
                },
                [user.settings.email, ],
            )
        return count

    def handle(self, *args, **options):
        days_list = [
            settings.REMOVE_PASSIVE_USERS_REMINDING_DAYS,
            settings.REMOVE_PASSIVE_USERS_REMINDING_DAYS_2,
        ]

        result = []
        for reminding_days in days_list:
            last_login = date.today() - timedelta(days=reminding_days)
            result.append((last_login, self.remind_users(last_login, reminding_days)))

        for last_login, count in result:
            self.stdout.write('Successfully reminded {} users with latest '
                              'login {}'.format(count, last_login))
