# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from libs.moderation.models import ModeratedObject, MODERATION_STATUS_PENDING
from nuka.utils import send_email_to_multiple_receivers
from organization.models import Organization


class Command(BaseCommand):
    help = 'Removes unactivated organizations'

    def handle(self, *args, **options):
        archive_date = date.today() - timedelta(
            days=settings.UNACTIVE_ORGANIZATIONS_REMOVING_DAYS
        )

        ct_id = ContentType.objects.get_for_model(Organization).pk
        moderated_objects = ModeratedObject.objects.filter(
            content_type_id=ct_id,
            date_updated__lte=archive_date,
            moderation_status=MODERATION_STATUS_PENDING
        )

        for o in moderated_objects:
            send_email_to_multiple_receivers(
                _("Organisaatio poistettu"),
                "organization/email/unactivated_removed.txt",
                {"organization": o.content_object.name},
                o.content_object.admins.all()
            )
            o.content_object.delete()
            o.delete()

        self.stdout.write('removed {} organizations in que since {}'.format(
            moderated_objects.count(),
            archive_date
        ))
