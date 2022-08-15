# coding=utf-8

from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils import timezone

from account.models import User, GROUP_NAME_MODERATORS


class Command(BaseCommand):
    help = 'Removes outdated moderator rights'

    def handle(self, *args, **options):
        users = User.objects.filter(
            groups__name=GROUP_NAME_MODERATORS,
            moderator_rights_valid_until__lt=timezone.now().date()
        )
        group = Group.objects.get(name=GROUP_NAME_MODERATORS)

        for user in users:
            group.user_set.remove(user)

        self.stdout.write('Successfully removed moderator rights from {} users'.format(
            users.count()))
