# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('nkmoderation', '0003_auto_20150116_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moderationreason',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=True,
        ),
    ]
