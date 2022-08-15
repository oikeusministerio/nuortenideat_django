# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.core.management.base import BaseCommand

from content.models import Idea
from content.utils import transfer_idea_forward


class Command(BaseCommand):
    def handle(self, *args, **options):
        transfer_date = date.today() + timedelta(days=1)
        conditions = {
            'auto_transfer_at__lt': transfer_date,
            'status__lt': Idea.STATUS_TRANSFERRED,
            'visibility': Idea.VISIBILITY_PUBLIC,
        }
        ideas = Idea._base_manager.filter(**conditions)

        if not ideas:
            print 'Ei ideoita'
        else:
            for obj in ideas:
                transfer_idea_forward(obj.pk)
