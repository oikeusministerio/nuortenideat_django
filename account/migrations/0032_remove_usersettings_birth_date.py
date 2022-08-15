# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0031_auto_20180828_1430'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='birth_date',
        ),
    ]
