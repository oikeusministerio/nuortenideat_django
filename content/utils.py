# coding=utf-8

from __future__ import unicode_literals

import logging

from datetime import date, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.mail.message import EmailMessage
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.utils.translation import ugettext as _, activate
from django.utils import timezone
from django.conf import settings

from account.models import User
from content.models import Idea, IdeaSurvey
from nkvote.models import Gallup
from nuka.utils import send_email

logger = logging.getLogger(__package__)


def idea_receivers(idea, contact_persons=False):
    if idea.initiator_organization:
        receivers = list(idea.initiator_organization.admins.all())
    else:
        receivers = list(idea.owners.all())

    if contact_persons:
        receivers += [
            admin
            for organization in idea.target_organizations.all()
            for admin in organization.admins.all()
        ]

    return receivers


def warn_unpublished_ideas(warn_date, archive_date):
    ideas = Idea._base_manager.filter(
        Q(status=Idea.STATUS_DRAFT) &
        Q(visibility=Idea.VISIBILITY_DRAFT) &
        Q(created__lt=warn_date + timedelta(days=1)) &
        Q(created__gte=warn_date)
    )

    unpublished_days = (date.today() - warn_date).days
    archive_days = (warn_date - archive_date).days

    for idea in ideas:
        for receiver in idea_receivers(idea):
            send_email(
                _("Idea '{name}' on ollut julkaisematon {days} päivää.".format(
                    name=idea.title, days=unpublished_days)),
                "content/email/unpublished_warning.txt",
                {
                    "idea": idea,
                    "unpublished_days": unpublished_days,
                    "archive_days": archive_days,
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Varoitus julkaisemattoman idean %d arkistoinnista lähetetetty "
                        "osoitteeseen %s.", idea.pk, receiver.settings.email)


def archive_unpublished_ideas(archive_date):
    ideas = Idea._base_manager.filter(
        status=Idea.STATUS_DRAFT, created__lt=archive_date + timedelta(days=1)
    ).exclude(
        visibility=Idea.VISIBILITY_ARCHIVED
    )
    for idea in ideas:
        idea.visibility = Idea.VISIBILITY_ARCHIVED
        close_idea_target_gallups(idea)
        close_idea_target_surveys(idea)
        idea.save()
        logger.info("Idea %s arkistoitu.", idea.pk)
        for receiver in idea_receivers(idea):
            send_email(
                _("Idea '%s' on arkistoitu.") % idea,
                "content/email/unpublished_archived.txt",
                {
                    "idea": idea,
                    "published_days": (date.today() - archive_date).days,
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Sähköposti idean %d arkistoimisesta lähetetetty "
                        "osoitteeseen %s.", idea.pk, receiver.settings.email)


def remind_untransferred_ideas(remind_date, archive_date):
    ideas = Idea._base_manager.filter(
        published__startswith=remind_date,
        status=Idea.STATUS_PUBLISHED,
        visibility=Idea.VISIBILITY_PUBLIC,
        auto_transfer_at__isnull=True
    )

    published_days = (date.today() - remind_date).days
    archive_days = (remind_date - archive_date).days
    for idea in ideas:
        for receiver in idea_receivers(idea, contact_persons=True):
            send_email(
                _("Muistutus idean '%s' viemisestä eteenpäin.") % idea.title,
                "content/email/untransferred_reminder.txt",
                {
                    "idea": idea,
                    "published_days": published_days,
                    "archive_days": archive_days,
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Muistutus idean %d viemisestä eteenpäin lähetetetty "
                        "osoitteeseen %s.", idea.pk, receiver.settings.email)


def warn_untransferred_ideas(warn_date, archive_date):
    ideas = Idea._base_manager.filter(
        published__startswith=warn_date,
        status=Idea.STATUS_PUBLISHED,
        visibility=Idea.VISIBILITY_PUBLIC,
        auto_transfer_at__isnull=True
    )

    published_days = (date.today() - warn_date).days
    archive_days = (warn_date - archive_date).days

    for idea in ideas:
        for receiver in idea_receivers(idea, contact_persons=True):
            send_email(
                _("Muistutus idean '%s' viemisestä eteenpäin.") % idea.title,
                "content/email/untransferred_warning.txt",
                {
                    "idea": idea,
                    "published_days": published_days,
                    "archive_days": archive_days,
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Muistutus idean %d viemisestä eteenpäin lähetetetty "
                        "osoitteeseen %s.", idea.pk, receiver.settings.email)


def archive_untransferred_ideas(archive_date):
    ideas = Idea._base_manager.filter(
        published__lt=archive_date + timedelta(days=1),
        status=Idea.STATUS_PUBLISHED,
        visibility=Idea.VISIBILITY_PUBLIC,
        auto_transfer_at__isnull=True
    )
    for idea in ideas:
        idea.visibility = Idea.VISIBILITY_ARCHIVED
        idea.save()
        close_idea_target_gallups(idea)
        close_idea_target_surveys(idea)
        logger.info("Idea %s arkistoitu.", idea.pk)
        for receiver in idea_receivers(idea, contact_persons=True):
            send_email(
                _("Idea '%s' on arkistoitu.") % idea,
                "content/email/untransferred_archived.txt",
                {
                    "idea": idea,
                    "published_days": (date.today() - archive_date).days,
                },
                [receiver.settings.email],
                receiver.settings.language
            )
            logger.info("Sähköposti idean %d arkistoimisesta lähetetetty "
                        "osoitteeseen %s.", idea.pk, receiver.settings.email)


def close_idea_target_gallups(idea):
    for g in idea.gallup_set.all():
        if g.status == Gallup.STATUS_OPEN:
            g.status = Gallup.STATUS_CLOSED
            g.closed = timezone.now()
            g.save()

    return idea.gallup_set.all()


def close_idea_target_surveys(idea):
    for s in idea.idea_surveys.all():
        if s.status == IdeaSurvey.STATUS_OPEN:
            s.status = IdeaSurvey.STATUS_CLOSED
            s.closed = timezone.now()
            s.save()
    return idea.idea_surveys.all()


def transfer_idea_forward(idea_pk):
    from content.views import IdeaPDFCeleryView

    try:
        idea = Idea._base_manager.get(pk=idea_pk)
    except ObjectDoesNotExist:
        return None

    request = RequestFactory().get('/whatever/')
    request.LANGUAGE_CODE = settings.LANGUAGE_CODE
    activate(settings.LANGUAGE_CODE)

    try:
        request.user = User.objects.get(pk=idea.owner_ids.first())
        mail_ctx = {
            'sender_name': ", ".join(idea.owner_names()),
            'sender_email': ", ".join(idea.owner_emails()),
            'idea_url': idea.get_absolute_url()
        }
    except ObjectDoesNotExist:
        mail_ctx = {
            'sender_name': "Poistunut käyttäjä",
            'sender_email': "",
            'idea_url': idea.get_absolute_url()
        }

    view = IdeaPDFCeleryView.as_view(idea=idea)
    resp = view(request=request)

    tmp_file_html = resp.render_to_temporary_file(resp.template_name)
    tmp_file = resp.convert_to_pdf(tmp_file_html.name)

    send_email(
        title=_("Idea liitteenä - nuortenideat.fi"),
        msg_template='content/email/transfer_idea_email_default_text.txt',
        msg_ctx=mail_ctx,
        receivers=idea.get_target_organization_email_list(),
        attachments=[('idea.pdf', tmp_file, )]
    )

    idea.transfer_idea()
    idea.close_surveys()

    return idea


def remind_admins_for_uncompleted_ideas(transfer_date):
    ideas = Idea._base_manager.filter(
        status=Idea.STATUS_TRANSFERRED,
        transferred__year=transfer_date.year,
        transferred__month=transfer_date.month,
        transferred__day=transfer_date.day,
    ).exclude(
        visibility=Idea.VISIBILITY_ARCHIVED
    )

    activate(settings.LANGUAGE_CODE)

    for idea in ideas:
        receivers = idea.get_target_organization_email_list()
        send_email(
            _("Muistutus idean '%s' vastauksen kirjaamisesta.") % idea.title,
            "content/email/uncompleted_reminder.txt",
            {
                "idea": idea,
                "idea_url": idea.get_absolute_url(),
                "transferred_days": (date.today() - transfer_date).days,
            },
            receivers,
        )
        logger.info("Muistutus idean %d vastauksen kirjaamisesta lähetetetty "
                    "osoitteeseen %s.", idea.pk, ", ".join(receivers))
