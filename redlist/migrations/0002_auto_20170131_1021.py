# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-31 08:21
from __future__ import unicode_literals

import django.contrib.postgres.fields.hstore
import django.contrib.postgres.fields.ranges
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('redlist', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assessment',
            old_name='population_size',
            new_name='area_occupancy',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='population_trend_future',
            new_name='extent_occurrence',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='population_trend_past',
            new_name='population_current',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='taxa',
            new_name='taxon',
        ),
        migrations.AddField(
            model_name='assessment',
            name='population_future',
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='population_past',
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessment',
            name='temp_field',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='actionnature',
            name='verbose',
            field=models.TextField(blank=True),
        ),
    ]