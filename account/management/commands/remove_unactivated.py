# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.conf import settings

from account.models import User


class Command(BaseCommand):
    help = 'Removes registered users that have not been activated within %s days' % \
           settings.UNACTIVATED_USERS_REMOVING_DAYS

    def handle(self, *args, **options):
        date_limit = date.today() - timedelta(
            days=settings.UNACTIVATED_USERS_REMOVING_DAYS)

        users = User.objects.filter(
            status=User.STATUS_AWAITING_ACTIVATION,
            joined__lte=date_limit
        )
        count = users.count()
        users.delete()

        self.stdout.write('Successfully removed {} unactive users who joined '
                          'before {}'.format(count, date_limit))
