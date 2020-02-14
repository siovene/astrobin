# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-02-14 10:56
from __future__ import unicode_literals

from django.db import migrations, models

import astrobin.models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0040_image_add_fits_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagerevision',
            name='fits_file',
            field=models.ImageField(max_length=256, null=True, upload_to=astrobin.models.image_upload_path),
        ),
    ]