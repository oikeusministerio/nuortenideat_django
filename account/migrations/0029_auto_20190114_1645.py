# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0028_auto_20160808_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientidentifier',
            name='user_agent',
            field=models.CharField(max_length=500),
        ),
    ]
