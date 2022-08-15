# coding=utf-8

from __future__ import unicode_literals

from celery.app import shared_task
from django.core.management import call_command


@shared_task
def warn_unpublished():
    call_command("warn_unpublished")


@shared_task
def archive_unpublished():
    call_command("archive_unpublished")


@shared_task
def remind_untransferred():
    call_command("remind_untransferred")


@shared_task
def warn_untransferred():
    call_command("warn_untransferred")


@shared_task
def archive_untransferred():
    call_command("archive_untransferred")


@shared_task
def transfer_idea():
    call_command("transfer_idea")


@shared_task
def remind_uncompleted():
    call_command("remind_uncompleted")


@shared_task
def remove_old_drafts():
    call_command("remove_old_drafts")
