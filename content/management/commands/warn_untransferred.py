# conding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.conf import settings
from django.core.management.base import BaseCommand

from content.utils import warn_untransferred_ideas


class Command(BaseCommand):
    def handle(self, *args, **options):
        warn_date = date.today() - timedelta(days=settings.UNTRANSFERRED_WARNING_DAYS)
        archive_date = date.today() - timedelta(
            days=settings.UNTRANSFERRED_ARCHIVING_DAYS
        )
        warn_untransferred_ideas(warn_date, archive_date)
