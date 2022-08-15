# coding=utf-8

from __future__ import unicode_literals

from celery.app import shared_task
from django.core.management import call_command


@shared_task
def remove_unactivated():
    call_command("remove_unactivated")


@shared_task
def remind_passive():
    call_command("remind_passive")


@shared_task
def remove_passive():
    call_command("remove_passive")


@shared_task
def remind_moderator_rights():
    call_command("remind_moderator_rights")


@shared_task
def remove_moderator_rights():
    call_command("remove_moderator_rights")


