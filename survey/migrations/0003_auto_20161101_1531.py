# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20160808_1203'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='surveysubmission',
            unique_together=set([]),
        ),
    ]
