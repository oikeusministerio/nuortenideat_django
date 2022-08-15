# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.conf import settings

from account.models import User, GROUP_NAME_MODERATORS


class Command(BaseCommand):
    help = 'Sets default value for moderator_rights_valid_until-field. Should be ' \
           'needed only once'

    def handle(self, *args, **options):
        users = User.objects.filter(groups__name=GROUP_NAME_MODERATORS,
                                    moderator_rights_valid_until__isnull=True)

        valid_until = date.today() + timedelta(
            days=settings.MODERATOR_RIGHTS_VALID_REMINDING_DAYS + 2)

        users.update(moderator_rights_valid_until=valid_until)

        self.stdout.write('Successfully added {} moderators validity time to {}'.format(
            users.count(), valid_until))
