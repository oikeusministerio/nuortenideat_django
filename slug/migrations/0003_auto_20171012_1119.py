# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slug', '0002_objectslug_original_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objectslug',
            name='slug',
            field=models.SlugField(max_length=255),
        ),
    ]
