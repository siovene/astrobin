# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-11-12 15:10
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import nested_comments.models


class Migration(migrations.Migration):

    dependencies = [
        ('nested_comments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nestedcomment',
            name='author',
            field=models.ForeignKey(editable=False, on_delete=models.SET(nested_comments.models.get_sentinel_user), to=settings.AUTH_USER_MODEL),
        ),
    ]