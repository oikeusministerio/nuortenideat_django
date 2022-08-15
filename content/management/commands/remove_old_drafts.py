# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.conf import settings

from content.models import Idea


class Command(BaseCommand):
    def handle(self, *args, **options):
        date_limit = date.today() - timedelta(days=settings.IDEA_DRAFTS_REMOVING_DAYS)
        conditions = {
            'created__lte': date_limit,
            'status': Idea.STATUS_DRAFT,
        }
        ideas = Idea._base_manager.filter(**conditions)
        if not ideas:
            print 'Ei ideoita'
        else:
            self.stdout.write('Trying to remove {} ideas'.format(ideas.count()))
            for obj in ideas:
                obj.delete()
        self.stdout.write('Done')
