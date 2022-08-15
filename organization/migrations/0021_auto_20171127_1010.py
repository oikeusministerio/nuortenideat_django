# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0020_auto_20160527_1140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='type',
            field=models.SmallIntegerField(verbose_name='tyyppi', choices=[(0, 'Tuntematon'), (1, 'Koko Suomi'), (3, 'J\xe4rjest\xf6'), (4, 'Kunta'), (5, 'Koulu tai muu oppilaitos'), (6, 'Nuorten vaikuttajaryhm\xe4'), (10, 'Muu')]),
        ),
    ]
