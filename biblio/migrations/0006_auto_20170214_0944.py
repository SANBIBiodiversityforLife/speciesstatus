# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-02-14 07:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('redlist', '0008_auto_20170210_1055'),
        ('taxa', '0014_auto_20170210_1158'),
        ('biblio', '0005_auto_20170203_1034'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='editors',
        ),
        migrations.RemoveField(
            model_name='book',
            name='publisher',
        ),
        migrations.RemoveField(
            model_name='book',
            name='reference_ptr',
        ),
        migrations.RemoveField(
            model_name='bookchapter',
            name='parent_book',
        ),
        migrations.RemoveField(
            model_name='bookchapter',
            name='reference_ptr',
        ),
        migrations.RemoveField(
            model_name='journal',
            name='publisher',
        ),
        migrations.RemoveField(
            model_name='journalarticle',
            name='journal',
        ),
        migrations.RemoveField(
            model_name='journalarticle',
            name='reference_ptr',
        ),
        migrations.RemoveField(
            model_name='thesis',
            name='reference_ptr',
        ),
        migrations.RemoveField(
            model_name='webpage',
            name='reference_ptr',
        ),
        migrations.DeleteModel(
            name='Book',
        ),
        migrations.DeleteModel(
            name='BookChapter',
        ),
        migrations.DeleteModel(
            name='Journal',
        ),
        migrations.DeleteModel(
            name='JournalArticle',
        ),
        migrations.DeleteModel(
            name='Publisher',
        ),
        migrations.DeleteModel(
            name='Thesis',
        ),
        migrations.DeleteModel(
            name='WebPage',
        ),
    ]
