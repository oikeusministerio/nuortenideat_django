# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0034_idea_auto_transfer_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionaldetail',
            name='type',
            field=models.SmallIntegerField(default=0, choices=[(0, 'lis\xe4tieto'), (1, 'VASTAUS'), (2, 'Viety eteenp\xe4in')]),
        ),
        migrations.AlterField(
            model_name='idea',
            name='auto_transfer_at',
            field=models.DateField(default=None, null=True, verbose_name='Idean vienti eteenp\xe4in automaattisesti', blank=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'Luonnos'), (3, 'Julkaistu'), (6, 'Viety eteenp\xe4in'), (9, 'Vastaus annettu')]),
        ),
    ]
