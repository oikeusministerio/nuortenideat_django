# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from account.models import User
from content.models import Initiative


class Command(BaseCommand):
    help = 'Removes registered users that have not been active within %s days' % \
           settings.REMOVE_PASSIVE_USERS_DAYS

    def detach_from_initiative(self, user):
        initiatives = Initiative.objects.filter(creator=user.pk)
        for i in initiatives:
            i.creator = None
            i.save()

    def handle(self, *args, **options):
        date_limit = date.today() - timedelta(
            days=settings.REMOVE_PASSIVE_USERS_DAYS)

        users = User.objects.filter(
            Q(last_login__lte=date_limit) |
            Q(last_login__isnull=True,
              joined__lte=date_limit,
              status=User.STATUS_ACTIVE)
        )
        count = users.count()
        failed = []
        for u in users:
            try:
                self.detach_from_initiative(u)
                u.delete()
            except Exception as inst:
                failed.append(u)
                print type(inst)
                print "{} not deleted".format(u)

        self.stdout.write('Successfully removed {} passive users with latest login '
                          'before {}'.format(count - len(failed), date_limit))
        self.stdout.write('Failed deleting {} user/s'.format(len(failed)))
