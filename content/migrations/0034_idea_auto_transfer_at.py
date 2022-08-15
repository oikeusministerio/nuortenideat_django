# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0033_ideasurvey_answer_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='idea',
            name='auto_transfer_at',
            field=models.DateField(default=None, null=True, blank=True),
        ),
    ]
