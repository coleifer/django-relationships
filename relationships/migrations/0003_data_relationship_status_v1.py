# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def create_relationship_status(apps, schema_editor):

	RelationshipStatus = apps.get_model('relationships', "RelationshipStatus")

	rs = RelationshipStatus.objects.filter(pk=1)
	if(rs.exists()):
		rs = rs[0]
		rs.name = 'Following'
		rs.to_slug = 'followers'
		rs.from_slug = 'following'
		rs.symmetrical_slug = 'friends'
		rs.verb = 'follow'
		rs.save()
	else:
		RelationshipStatus.objects.create(
				name='Following',
				to_slug='followers',
				from_slug='following',
				symmetrical_slug='friends',
				verb='follow',
				)

	rs = RelationshipStatus.objects.filter(pk=2)
	if(rs.exists()):
		rs = rs[0]
		rs.name = 'Blocking'
		rs.to_slug = 'blockers'
		rs.from_slug = 'blocking'
		rs.symmetrical_slug = '!'
		rs.verb = 'block'
		rs.login_required = True
		rs.private = True
		rs.save()
	else:
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
