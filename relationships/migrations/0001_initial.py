# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from relationships.utils import user_model_label, user_orm_label, User


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RelationshipStatus'
        db.create_table(u'relationships_relationshipstatus', (
            ('id', self.gf('relationships.models.SIDField')(default='R_3dbae02132e5841d', unique=True, max_length=18, primary_key=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('verb', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('from_slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('to_slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('symmetrical_slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('login_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('private', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'relationships', ['RelationshipStatus'])

        # Adding model 'Relationship'
        db.create_table(u'relationships_relationship', (
            ('id', self.gf('relationships.models.SIDField')(default='R_3d123164fdd12339', unique=True, max_length=18, primary_key=True, db_index=True)),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_users', to=orm[user_orm_label])),
            ('to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_users', null=True, to=orm[user_orm_label])),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['relationships.RelationshipStatus'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('weight', self.gf('django.db.models.fields.FloatField')(default=1.0, null=True, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='relationships', to=orm['sites.Site'])),
            ('extra_data', self.gf('jsonfield.fields.JSONField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'relationships', ['Relationship'])

        # Adding unique constraint on 'Relationship', fields ['from_user', 'to_user', 'status', 'site']
        db.create_unique(u'relationships_relationship', ['from_user_id', 'to_user_id', 'status_id', 'site_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Relationship', fields ['from_user', 'to_user', 'status', 'site']
        db.delete_unique(u'relationships_relationship', ['from_user_id', 'to_user_id', 'status_id', 'site_id'])

        # Deleting model 'RelationshipStatus'
        db.delete_table(u'relationships_relationshipstatus')

        # Deleting model 'Relationship'
        db.delete_table(u'relationships_relationship')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        # http://kevindias.com/writing/django-custom-user-models-south-and-reusable-apps/
        user_model_label: {
            # We've accounted for changes to:
            # the app name, table name, pk attribute name, pk column name.
            # The only assumption left is that the pk is an AutoField (see below)
            'Meta': { 'object_name': User.__name__, 'db_table': "'%s'" % User._meta.db_table },
            User._meta.pk.attname: ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'db_column': "'%s'" % User._meta.pk.column})
        },
        u'relationships.relationship': {
            'Meta': {'ordering': "('created',)", 'unique_together': "(('from_user', 'to_user', 'status', 'site'),)", 'object_name': 'Relationship'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'extra_data': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': u"orm['%s']" % user_orm_label}),
            'id': ('relationships.models.SIDField', [], {'default': "'R_5eaac4757a9372d7'", 'unique': 'True', 'max_length': '18', 'primary_key': 'True', 'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'relationships'", 'to': u"orm['sites.Site']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['relationships.RelationshipStatus']"}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'null': 'True', 'to': u"orm['%s']" % user_orm_label}),
            'weight': ('django.db.models.fields.FloatField', [], {'default': '1.0', 'null': 'True', 'blank': 'True'})
        },
        u'relationships.relationshipstatus': {
            'Meta': {'ordering': "('name',)", 'object_name': 'RelationshipStatus'},
            'from_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('relationships.models.SIDField', [], {'default': "'R_b09c77722153ba56'", 'unique': 'True', 'max_length': '18', 'primary_key': 'True', 'db_index': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'symmetrical_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'to_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['relationships']