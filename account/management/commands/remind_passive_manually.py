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
            Q(last_login__lt=last_login) |
            Q(last_login__isnull=True,
              joined__lt=last_login,
              status=User.STATUS_ACTIVE)
        )
        count = users.count()
        activate(settings.LANGUAGE_CODE)

        for user in users:
            send_email(
                _("Varoitus käyttäjätilin poistamisesta."),
                "account/email/remind_passive_users.txt",
                {
                    "username": user.username,
                    "days_until": 14,
                },
                [user.settings.email, ],
            )
        return count

    def handle(self, *args, **options):
        reminding_days = 14

        last_login = date(2017, 5, 26)
        count = self.remind_users(last_login, reminding_days)

        self.stdout.write('Successfully reminded {} users with latest '
                          'login {}'.format(count, last_login))


# TÄMÄ ajetaan kaksi kertaa ja muutetaan reminding days 14 tokalla kerralla
# eka ajo 13.5. ja toka 29.5.
# 11.6. aamulla poisto päälle, tai jos illalla niin manuaalinen ajo kerran



"""
Tämän voi laittaa suoraan tuotantoon. remove_passive ei.
Tee tästä command joka ajetaan manuaalisesti 2 kertaa. 
Päivämäärä less than tuotantoonvientipäivä - REMOVE_PASSIVE_USERS_REMINDING_DAYS  

exact date esim. 1.3.2019
1 remind last_login == 1.3.2019 - REMOVE_PASSIVE_USERS_DAYS = 1.3.2017
2 remind last_login == 1.3.2019 - REMOVE_PASSIVE_USERS_DAYS_2 = 15.3.2017 kulkee esim. 14 päivää jäljessä

vanhemmat - ajetaan heti
1 remind last_login < 1.3.2017
2 remind 14 pv:n kuluttua ja last_login < 1.3.2017

TODO: poista tämä file kun ajettu
"""
