# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import nkpicturecarousel.models


class Migration(migrations.Migration):

    dependencies = [
        ('nkpicturecarousel', '0002_picturecarouselimage_original'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picturecarouselimage',
            name='original',
            field=models.ImageField(upload_to=nkpicturecarousel.models._carousel_pic_path, null=True, verbose_name='kuva'),
        ),
    ]
