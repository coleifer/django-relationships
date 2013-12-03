from south.db import db
from relationships.models import *


class Migration:

    def forwards(self, orm):

        # Adding model 'RelationshipStatus'
        db.create_table('relationships_relationshipstatus', (
            ('id', orm['relationships.RelationshipStatus:id']),
            ('name', orm['relationships.RelationshipStatus:name']),
            ('verb', orm['relationships.RelationshipStatus:verb']),
            ('from_slug', orm['relationships.RelationshipStatus:from_slug']),
            ('to_slug', orm['relationships.RelationshipStatus:to_slug']),
            ('symmetrical_slug', orm['relationships.RelationshipStatus:symmetrical_slug']),
            ('login_required', orm['relationships.RelationshipStatus:login_required']),
            ('private', orm['relationships.RelationshipStatus:private']),
        ))
        db.send_create_signal('relationships', ['RelationshipStatus'])

        # Adding model 'Relationship'
        db.create_table('relationships_relationship', (
            ('id', orm['relationships.Relationship:id']),
            ('from_user', orm['relationships.Relationship:from_user']),
            ('to_user', orm['relationships.Relationship:to_user']),
            ('status', orm['relationships.Relationship:status']),
            ('created', orm['relationships.Relationship:created']),
        ))
        db.send_create_signal('relationships', ['Relationship'])

        # Creating unique_together for [from_user, to_user, status] on Relationship.
        db.create_unique('relationships_relationship', ['from_user_id', 'to_user_id', 'status_id'])

    def backwards(self, orm):

        # Deleting unique_together for [from_user, to_user, status] on Relationship.
        db.delete_unique('relationships_relationship', ['from_user_id', 'to_user_id', 'status_id'])

        # Deleting model 'RelationshipStatus'
        db.delete_table('relationships_relationshipstatus')

        # Deleting model 'Relationship'
        db.delete_table('relationships_relationship')

    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'relationships': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'relationships.relationship': {
            'Meta': {'unique_together': "(('from_user', 'to_user', 'status'),)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['relationships.RelationshipStatus']"}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'relationships.relationshipstatus': {
            'from_slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'symmetrical_slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'to_slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['relationships']
