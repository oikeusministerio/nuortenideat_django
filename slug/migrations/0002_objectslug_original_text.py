# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slug', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='objectslug',
            name='original_text',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]
