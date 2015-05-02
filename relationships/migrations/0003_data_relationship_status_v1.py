# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def create_relationship_status(apps, schema_editor):

	RelationshipStatus = apps.get_model('relationships', "RelationshipStatus")

	RelationshipStatus.objects.create(
			name='Following',
			to_slug='followers',
			from_slug='following',
			symmetrical_slug='friends',
			verb='follow',
			)

	RelationshipStatus.objects.create(
			name='Blocking',
			to_slug='blockers',
			from_slug='blocking',
			symmetrical_slug='!',
			verb='block',
			login_required=True,
			private=True,
			)

class Migration(migrations.Migration):

    dependencies = [
        ('relationships', '0002_relationship_updated_at'),
    ]

    operations = [
    	migrations.RunPython(create_relationship_status),
    ]
