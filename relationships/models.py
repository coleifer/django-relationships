import django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models, connection
from django.db.models.fields.related import create_many_related_manager, ManyToManyRel
from django.utils.translation import ugettext_lazy as _


class RelationshipStatusManager(models.Manager):
    # convenience methods to handle some default statuses
    def following(self):
        return self.get(from_slug='following')

    def blocking(self):
        return self.get(from_slug='blocking')

    def by_slug(self, status_slug):
        return self.get(
            models.Q(from_slug=status_slug) | 
            models.Q(to_slug=status_slug) | 
            models.Q(symmetrical_slug=status_slug))


class RelationshipStatus(models.Model):
    name = models.CharField(_('name'), max_length=100)
    verb = models.CharField(_('verb'), max_length=100)
    from_slug = models.CharField(_('from slug'), max_length=100,
        help_text=_("Denote the relationship from the user, i.e. 'following'"))
    to_slug = models.CharField(_('to slug'), max_length=100,
        help_text=_("Denote the relationship to the user, i.e. 'followers'"))
    symmetrical_slug = models.CharField(_('symmetrical slug'), max_length=100,
        help_text=_("When a mutual relationship exists, i.e. 'friends'"))
    login_required = models.BooleanField(_('login required'), default=False,
        help_text=_("Users must be logged in to see these relationships"))
    private = models.BooleanField(_('private'), default=False,
        help_text=_("Only the user who owns these relationships can see them"))

    objects = RelationshipStatusManager()
    
    class Meta:
        ordering = ('name',)
        verbose_name = _('Relationship status')
        verbose_name_plural = _('Relationship statuses')

    def __unicode__(self):
        return self.name


class Relationship(models.Model):
    from_user = models.ForeignKey(User,
        related_name='from_users', verbose_name=_('from user'))
    to_user = models.ForeignKey(User,
        related_name='to_users', verbose_name=_('to user'))
    status = models.ForeignKey(RelationshipStatus, verbose_name=_('status'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    site = models.ForeignKey(Site, default=settings.SITE_ID,
        verbose_name=_('site'), related_name='relationships')

    class Meta:
        unique_together = (('from_user', 'to_user', 'status', 'site'),)
        ordering = ('created',)
        verbose_name = _('Relationship')
        verbose_name_plural = _('Relationships')

    def __unicode__(self):
        return (_('Relationship from %(from_user)s to %(to_user)s')
                % { 'from_user': self.from_user.username,
                    'to_user': self.to_user.username})

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
            status=status,
            site=Site.objects.get_current())
        return relationship

    def remove(self, user, status=None):
        if not status:
            status = RelationshipStatus.objects.following()
        Relationship.objects.filter(
            from_user=self.instance, 
            to_user=user,
            status=status,
            site__pk=settings.SITE_ID).delete()
        return
    
    def get_relationships(self, status):
        return User.objects.filter(
            to_users__from_user=self.instance,
            to_users__status=status,
            to_users__site__pk=settings.SITE_ID)
    
    def get_related_to(self, status):
        return User.objects.filter(
            from_users__to_user=self.instance,
            from_users__status=status,
            from_users__site__pk=settings.SITE_ID)

    def get_symmetrical(self, status):
        return User.objects.filter(
            to_users__status=status, 
            to_users__from_user=self.instance,
            to_users__site__pk=settings.SITE_ID,
            from_users__status=status, 
            from_users__to_user=self.instance,
            from_users__site__pk=settings.SITE_ID)
    
    def only_to(self, status):
        from_relationships = self.get_relationships(status)
        to_relationships = self.get_related_to(status)
        return to_relationships.exclude(pk__in=from_relationships.values_list('pk'))
    
    def only_from(self, status):
        from_relationships = self.get_relationships(status)
        to_relationships = self.get_related_to(status)
        return from_relationships.exclude(pk__in=to_relationships.values_list('pk'))
    
    def exists(self, user, status=None):
        query = {'to_users__from_user': self.instance,
                 'to_users__to_user': user,
                 'to_users__site__pk': settings.SITE_ID}
        if status:
            query['to_users__status'] = status
        return User.objects.filter(**query).count() != 0

    def symmetrical_exists(self, user, status=None):
        query = {'to_users__from_user': self.instance,
                 'to_users__to_user': user,
                 'to_users__site__pk': settings.SITE_ID,
                 'from_users__to_user': self.instance,
                 'from_users__from_user': user,
                 'from_users__site__pk': settings.SITE_ID}
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
