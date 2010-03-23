from django.contrib.auth.models import User
from django.db import models, connection
from django.db.models.fields.related import create_many_related_manager
from relationships.constants import *

class Relationship(models.Model):
    from_user = models.ForeignKey(User, related_name='from_users')
    to_user = models.ForeignKey(User, related_name='to_users')
    status = models.IntegerField(default=RELATIONSHIP_FOLLOWING, 
                                 choices=RELATIONSHIP_STATUSES)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('from_user', 'to_user', 'status'),)
        ordering = ('created',)

    def __unicode__(self):
        return 'Relationship from %s to %s' % (self.from_user.username,
                                               self.to_user.username)

field = models.ManyToManyField(User, through=Relationship, 
                               symmetrical=False, related_name='related_to')

class RelationshipManager(User._default_manager.__class__):
    def __init__(self, instance=None, *args, **kwargs):
        self.instance = instance

    def add(self, user, status=RELATIONSHIP_FOLLOWING):
        relationship, created = Relationship.objects.get_or_create(
            from_user=self.instance,
            to_user=user,
            status=status)
        return relationship

    def remove(self, user, status=RELATIONSHIP_FOLLOWING):
        Relationship.objects.filter(
            from_user=self.instance, 
            to_user=user,
            status=status).delete()
        return
    
    def get_relationships(self, status):
        return User.objects.filter(
            to_users__from_user=self.instance,
            to_users__status=status)
    
    def get_related_to(self, status):
        return User.objects.filter(
            from_users__to_user=self.instance,
            from_users__status=status)
    
    def following(self):
        return self.get_relationships(RELATIONSHIP_FOLLOWING)
    
    def followers(self):
        return self.get_related_to(RELATIONSHIP_FOLLOWING)
    
    def blocking(self):
        return self.get_relationships(RELATIONSHIP_BLOCKING)
    
    def blockers(self):
        return self.get_related_to(RELATIONSHIP_BLOCKING)

    def friends(self):
        return User.objects.filter(
            to_users__status=RELATIONSHIP_FOLLOWING, 
            to_users__from_user=self.instance,
            from_users__status=RELATIONSHIP_FOLLOWING, 
            from_users__to_user=self.instance)

RelatedManager = create_many_related_manager(RelationshipManager, Relationship)

class RelationshipsDescriptor(object):
    def __get__(self, instance, instance_type=None):
        qn = connection.ops.quote_name
        manager = RelatedManager(
            model=User,
            core_filters={'related_to__pk': instance._get_pk_val()},
            instance=instance,
            symmetrical=False,
            join_table=qn('relationships_relationship'),
            source_col_name=qn('from_user_id'),
            target_col_name=qn('to_user_id'),
        )
        return manager

#HACK
field.contribute_to_class(User, 'relationships')
setattr(User, 'relationships', RelationshipsDescriptor())
