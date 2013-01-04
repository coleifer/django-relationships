from south.db import db
from relationships.models import *


class Migration:

    def forwards(self, orm):

        # Deleting unique_together for [symmetrical_slug] on relationshipstatus.
        db.delete_unique('relationships_relationshipstatus', ['symmetrical_slug'])

        # Deleting unique_together for [from_slug] on relationshipstatus.
        db.delete_unique('relationships_relationshipstatus', ['from_slug'])

        # Deleting unique_together for [to_slug] on relationshipstatus.
        db.delete_unique('relationships_relationshipstatus', ['to_slug'])

        # Changing field 'RelationshipStatus.to_slug'
        # (to signature: django.db.models.fields.CharField(max_length=100))
        db.alter_column('relationships_relationshipstatus', 'to_slug', orm['relationships.relationshipstatus:to_slug'])

        # Changing field 'RelationshipStatus.symmetrical_slug'
        # (to signature: django.db.models.fields.CharField(max_length=100))
        db.alter_column('relationships_relationshipstatus', 'symmetrical_slug', orm['relationships.relationshipstatus:symmetrical_slug'])

        # Changing field 'RelationshipStatus.from_slug'
        # (to signature: django.db.models.fields.CharField(max_length=100))
        db.alter_column('relationships_relationshipstatus', 'from_slug', orm['relationships.relationshipstatus:from_slug'])

    def backwards(self, orm):

        # Changing field 'RelationshipStatus.to_slug'
        # (to signature: django.db.models.fields.SlugField(max_length=50, unique=True, db_index=True))
        db.alter_column('relationships_relationshipstatus', 'to_slug', orm['relationships.relationshipstatus:to_slug'])

        # Changing field 'RelationshipStatus.symmetrical_slug'
        # (to signature: django.db.models.fields.SlugField(max_length=50, unique=True, db_index=True))
        db.alter_column('relationships_relationshipstatus', 'symmetrical_slug', orm['relationships.relationshipstatus:symmetrical_slug'])

        # Changing field 'RelationshipStatus.from_slug'
        # (to signature: django.db.models.fields.SlugField(max_length=50, unique=True, db_index=True))
        db.alter_column('relationships_relationshipstatus', 'from_slug', orm['relationships.relationshipstatus:from_slug'])

        # Creating unique_together for [to_slug] on relationshipstatus.
        db.create_unique('relationships_relationshipstatus', ['to_slug'])

        # Creating unique_together for [from_slug] on relationshipstatus.
        db.create_unique('relationships_relationshipstatus', ['from_slug'])

        # Creating unique_together for [symmetrical_slug] on relationshipstatus.
        db.create_unique('relationships_relationshipstatus', ['symmetrical_slug'])

    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'relationships': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
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
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['sites.Site']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['relationships.RelationshipStatus']"}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'relationships.relationshipstatus': {
            'from_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'symmetrical_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'to_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['relationships']
