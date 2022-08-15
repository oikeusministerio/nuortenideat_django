from datetime import timedelta, date

from django.conf import settings
from django.core.management.base import BaseCommand

from content.utils import remind_admins_for_uncompleted_ideas


class Command(BaseCommand):
    def handle(self, *args, **options):
        transfer_date = date.today() - timedelta(
            days=settings.UNCOMPLETED_REMINDING_DAYS)
        remind_admins_for_uncompleted_ideas(transfer_date)
