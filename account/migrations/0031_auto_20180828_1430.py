# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_birth_years(apps, schema_editor):
    UserSettings = apps.get_model('account', 'UserSettings')

    for s in UserSettings.objects.all():
        s.birth_year = s.birth_date.year
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0030_usersettings_birth_year'),
    ]

    operations = [
        migrations.RunPython(set_birth_years)
    ]
