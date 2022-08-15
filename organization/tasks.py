# coding=utf-8

from __future__ import unicode_literals

from celery.app import shared_task
from django.core.management import call_command


@shared_task
def remove_unactivated_organizations():
    call_command('remove_unactivated_organizations')


@shared_task
def remind_unactivated_organizations():
    call_command('remind_unactivated_organizations')
