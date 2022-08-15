# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import account.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0032_remove_usersettings_birth_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='moderator_rights_valid_until',
            field=models.DateField(default=None, null=True, verbose_name='moderointioikeudet voimassa', blank=True),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='birth_year',
            field=models.IntegerField(default=2005, verbose_name='syntym\xe4vuosi', validators=[django.core.validators.MinValueValidator(1950), account.models.max_value_current_year]),
        ),
    ]
