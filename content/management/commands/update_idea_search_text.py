# coding=utf-8

from __future__ import unicode_literals
from django.core.management.base import BaseCommand

from content.models import Idea
from nuka.utils import strip_tags


class Command(BaseCommand):
    def handle(self, *args, **options):
        for o in Idea._base_manager.all():
            text = o.title.values() + o.description.values()
            o.search_text = ' '.join(map(strip_tags, text))
            o.save()
