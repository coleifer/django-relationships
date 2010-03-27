import django
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection
from django.db.models.fields.related import create_many_related_manager, ManyToManyRel


class RelationshipStatusManager(models.Manager):
    # convenience methods to handle some default statuses
    def following(self):
        return self.get(to_slug='following')

    def blocking(self):
        return self.get(to_slug='blocking')


class RelationshipStatus(models.Model):
    name = models.CharField(max_length=100)
    verb = models.CharField(max_length=100)
    from_slug = models.SlugField(unique=True)
    to_slug = models.SlugField(unique=True)
    symmetrical_slug = models.SlugField(unique=True)
    login_required = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    objects = RelationshipStatusManager()
    
    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Relationship(models.Model):
    from_user = models.ForeignKey(User, related_name='from_users')
    to_user = models.ForeignKey(User, related_name='to_users')
    status = models.ForeignKey(RelationshipStatus)
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
        super(RelationshipManager, self).__init__(*args, **kwargs)
        self.instance = instance

    def add(self, user, status=None):
        if not status:
            status = RelationshipStatus.objects.following()
        relationship, created = Relationship.objects.get_or_create(
            from_user=self.instance,
            to_user=user,
            status=status)
        return relationship

    def remove(self, user, status=None):
        if not status:
            status = RelationshipStatus.objects.following()
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

    def get_symmetrical(self, status):
        return User.objects.filter(
            to_users__status=status, 
            to_users__from_user=self.instance,
            from_users__status=status, 
            from_users__to_user=self.instance)
    
    def exists(self, user, status=None):
        query = {'to_users__from_user': self.instance,
                 'to_users__to_user': user}
        if status:
            query['to_users__status'] = status
        return User.objects.filter(**query).count() != 0

    def symmetrical_exists(self, user, status=None):
        query = {'to_users__from_user': self.instance,
                 'to_users__to_user': user,
                 'from_users__to_user': self.instance,
                 'from_users__from_user': user}
        if status:
            query.update({
                'to_users__status': status,
                'from_users__status': status})
        return User.objects.filter(**query).count() != 0

    # some defaults
    def following(self):
        return self.get_relationships(RelationshipStatus.objects.following())
    
    def followers(self):
        return self.get_related_to(RelationshipStatus.objects.following())
    
    def blocking(self):
        return self.get_relationships(RelationshipStatus.objects.blocking())
    
    def blockers(self):
        return self.get_related_to(RelationshipStatus.objects.blocking())

    def friends(self):
        return self.get_symmetrical(RelationshipStatus.objects.following())
    

if django.VERSION < (1, 2):

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

else:
    
    fake_rel = ManyToManyRel(
        to=User,
        through=Relationship)
        
    RelatedManager = create_many_related_manager(RelationshipManager, fake_rel)

    class RelationshipsDescriptor(object):
        def __get__(self, instance, instance_type=None):
            manager = RelatedManager(
                model=User,
                core_filters={'related_to__pk': instance._get_pk_val()},
                instance=instance,
                symmetrical=False,
                source_field_name='from_user',
                target_field_name='to_user'
            )
            return manager

#HACK
field.contribute_to_class(User, 'relationships')
setattr(User, 'relationships', RelationshipsDescriptor())
