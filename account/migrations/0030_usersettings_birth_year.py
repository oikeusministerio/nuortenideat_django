# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import account.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_auto_20190114_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='birth_year',
            field=models.IntegerField(default=1950, verbose_name='syntym\xe4vuosi', validators=[django.core.validators.MinValueValidator(1950), account.models.max_value_current_year]),
        ),
    ]
