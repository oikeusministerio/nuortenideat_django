# coding=utf-8

from __future__ import unicode_literals

from datetime import timedelta, date

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from account.models import User, GROUP_NAME_ADMINS, GROUP_NAME_MODERATORS
from libs.moderation.models import ModeratedObject, MODERATION_STATUS_PENDING
from nuka.utils import send_email_to_multiple_receivers
from organization.models import Organization


class Command(BaseCommand):
    help = 'Reminds moderators about expiring rights'

    def handle(self, *args, **options):
        reminding_date = date.today() - timedelta(
            days=settings.UNACTIVE_ORGANIZATIONS_WARNING_DAYS
        )

        ct_id = ContentType.objects.get_for_model(Organization).pk
        moderated_objects = ModeratedObject.objects.filter(
            content_type_id=ct_id,
            date_updated__startswith=str(reminding_date),
            moderation_status=MODERATION_STATUS_PENDING
        )

        moderators = User.objects.filter(groups__name__in=[GROUP_NAME_MODERATORS,
                                                           GROUP_NAME_ADMINS])
        for o in moderated_objects:
            send_email_to_multiple_receivers(
                _("Organisaatio aktivoimatta"),
                "organization/email/unactivated_not_activated.txt",
                {"organization": o.content_object.name},
                o.content_object.admins.all()
            )
            send_email_to_multiple_receivers(
                _("Organisaatio moderointijonossa"),
                "organization/email/unactivated_in_queue.txt",
                {"organization": o.content_object.name},
                moderators.all()
            )

        self.stdout.write('reminded of {} organizations: date {}'.format(
            moderated_objects.count(),
            reminding_date
        ))
