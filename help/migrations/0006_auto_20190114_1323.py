# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('help', '0005_auto_20161028_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instruction',
            name='connect_link_type',
            field=models.CharField(null=True, default=None, choices=[(None, 'ei mit\xe4\xe4n'), ('privacy-policy', 'tietosuojaseloste'), ('contact-details', 'yhteystiedot')], max_length=50, blank=True, unique=True),
        ),
    ]
