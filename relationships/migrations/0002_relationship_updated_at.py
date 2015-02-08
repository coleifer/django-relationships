# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('relationships', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationship',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 8, 3, 42, 38, 33802, tzinfo=utc), verbose_name='updated_at', auto_now=True),
            preserve_default=False,
        ),
    ]
