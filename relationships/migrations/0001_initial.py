# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('weight', models.FloatField(default=1.0, null=True, verbose_name='weight', blank=True)),
                ('from_user', models.ForeignKey(related_name='from_users', verbose_name='from user', to=settings.AUTH_USER_MODEL)),
                ('site', models.ForeignKey(related_name='relationships', default=1, verbose_name='site', to='sites.Site')),
            ],
            options={
                'ordering': ('created',),
                'verbose_name': 'Relationship',
                'verbose_name_plural': 'Relationships',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelationshipStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('verb', models.CharField(max_length=100, verbose_name='verb')),
                ('from_slug', models.CharField(help_text="Denote the relationship from the user, i.e. 'following'", max_length=100, verbose_name='from slug')),
                ('to_slug', models.CharField(help_text="Denote the relationship to the user, i.e. 'followers'", max_length=100, verbose_name='to slug')),
                ('symmetrical_slug', models.CharField(help_text="When a mutual relationship exists, i.e. 'friends'", max_length=100, verbose_name='symmetrical slug')),
                ('login_required', models.BooleanField(default=False, help_text='Users must be logged in to see these relationships', verbose_name='login required')),
                ('private', models.BooleanField(default=False, help_text='Only the user who owns these relationships can see them', verbose_name='private')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Relationship status',
                'verbose_name_plural': 'Relationship statuses',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='relationship',
            name='status',
            field=models.ForeignKey(verbose_name='status', to='relationships.RelationshipStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationship',
            name='to_user',
            field=models.ForeignKey(related_name='to_users', verbose_name='to user', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='relationship',
            unique_together=set([('from_user', 'to_user', 'status', 'site')]),
        ),
    ]
