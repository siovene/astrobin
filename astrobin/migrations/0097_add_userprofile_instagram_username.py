# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-12 22:58
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0096_add_userprofile_other_languages'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='instagram_username',
            field=models.CharField(
                blank=True,
                help_text="If you provide this, AstroBin will tag you on Instagram if it's sharing an image of yours.",
                max_length=30, null=True, validators=[
                    django.core.validators.MinLengthValidator(4),
                    django.core.validators.MaxLengthValidator(30),
                    django.core.validators.RegexValidator(
                        b'^@[\w](?!.*?\.{2})[\w.]{1,28}[\w]$',
                        'An Instagram username must be between 3 and 30 characters, start with an @ sign, and only '
                        'have letters, numbers, periods, and underlines.'
                    )
                ],
                verbose_name='Instagram username'),
        ),
    ]
