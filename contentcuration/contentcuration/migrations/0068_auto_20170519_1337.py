# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-05-19 20:37
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('contentcuration', '0067_auto_20170427_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='chef_tree',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='channel_chef', to='contentcuration.ContentNode'),
        ),
        migrations.AlterField(
            model_name='exercise',
            name='mastery_model',
            field=models.CharField(choices=[('do_all', 'Do all'), ('num_correct_in_a_row_2', '2 in a row'), ('num_correct_in_a_row_10', '10 in a row'), (
                'num_correct_in_a_row_3', '3 in a row'), ('num_correct_in_a_row_5', '5 in a row'), ('skill_check', 'Skill check'), ('m_of_n', 'M out of N')], default='do_all', max_length=200),
        ),
    ]
