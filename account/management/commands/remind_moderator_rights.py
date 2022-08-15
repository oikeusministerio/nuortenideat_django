# coding=utf-8

from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.conf import settings

from account.utils import send_moderator_rights_reminder_email


class Command(BaseCommand):
    help = 'Reminds moderators about expiring rights'

    def handle(self, *args, **options):
        users = send_moderator_rights_reminder_email(
            settings.MODERATOR_RIGHTS_VALID_REMINDING_DAYS)
        users2 = send_moderator_rights_reminder_email(
            settings.MODERATOR_RIGHTS_VALID_REMINDING_DAYS_2)
        self.stdout.write('Reminded {} moderators'.format(users.count() + users2.count()))
