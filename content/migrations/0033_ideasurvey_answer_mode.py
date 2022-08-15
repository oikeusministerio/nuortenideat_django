# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0032_auto_20160808_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='ideasurvey',
            name='answer_mode',
            field=models.SmallIntegerField(default=0, verbose_name='Vastaamisen asetukset', choices=[(0, 'Yksi vastaus osallistujaa kohden'), (1, 'Rajattomat vastaukset kirjautumattomille k\xe4ytt\xe4jille')]),
        ),
    ]
