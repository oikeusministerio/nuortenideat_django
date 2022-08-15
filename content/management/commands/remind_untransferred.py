# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.conf import settings
from django.core.management.base import BaseCommand

from content.utils import remind_untransferred_ideas


class Command(BaseCommand):
    def handle(self, *args, **options):
        remind_date = date.today() - timedelta(days=settings.UNTRANSFERRED_REMINDING_DAYS)
        archive_date = date.today() - timedelta(
            days=settings.UNTRANSFERRED_ARCHIVING_DAYS
        )
        remind_untransferred_ideas(remind_date, archive_date)
