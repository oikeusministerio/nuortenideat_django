# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import nkpicturecarousel.models


class Migration(migrations.Migration):

    dependencies = [
        ('nkpicturecarousel', '0003_auto_20200110_1538'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='picturecarouselimage',
            name='image_large',
        ),
        migrations.RemoveField(
            model_name='picturecarouselimage',
            name='image_medium',
        ),
        migrations.RemoveField(
            model_name='picturecarouselimage',
            name='image_small',
        ),
        migrations.AlterField(
            model_name='picturecarouselimage',
            name='original',
            field=models.ImageField(upload_to=nkpicturecarousel.models._carousel_pic_path, null=True, verbose_name='kuva'),
        ),
    ]
