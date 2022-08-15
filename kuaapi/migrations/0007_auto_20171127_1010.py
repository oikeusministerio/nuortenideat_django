# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kuaapi', '0006_auto_20141215_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kuainitiativestatus',
            name='status',
            field=models.CharField(max_length=20, choices=[('draft', 'Luonnos'), ('published', 'Julkaistu'), ('sent-to-municipality', 'L\xe4hetetty kuntaan'), ('decision-given', 'Vastaus annettu')]),
        ),
    ]
