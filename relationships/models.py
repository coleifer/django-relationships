from functools import partial
import random

import django
from django.core.exceptions import ValidationError
import jsonfield
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models, connection, transaction
from django.db.models.fields.related import create_many_related_manager, ManyToManyRel
from django.utils.translation import ugettext_lazy as _

from .compat import User
from south.modelsinspector import add_introspection_rules


def sid_creator(prefix):
    try:
        sid_creator.limit
    except AttributeError:
        sid_creator.limit = 16**SIDField.SID_LENGTH
    # http://stackoverflow.com/a/2782859/440060
    return prefix + '_' + ('%0{}x'.format(SIDField.SID_LENGTH) % random.randrange(sid_creator.limit))


class SIDField(models.CharField):
    SID_LENGTH = 16

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = SIDField.SID_LENGTH + 4
        kwargs['unique'] = True
        kwargs['db_index'] = True
        kwargs['editable'] = False
        kwargs['primary_key'] = True
        if 'prefix' in kwargs:
            self.prefix = kwargs.pop('prefix')
        super(SIDField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, virtual_only=False):
        if not hasattr(self, 'prefix'):
            self.prefix = cls.__name__[0].upper()
        self.default = partial(sid_creator, self.prefix)
        super(SIDField, self).contribute_to_class(cls, name, virtual_only=virtual_only)


rules = [
    (
        (SIDField,),
        [],
        {
            "db_index": [True, {"is_value": True}],
            "max_length": [SIDField.SID_LENGTH + 4, {"is_value": True}],
            "unique": [True, {"is_value": True}],
            "primary_key": [True, {"is_value": True}]
        },
    )
]
add_introspection_rules(rules, ["^relationships\.models\.SIDField"])


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
            models.Q(symmetrical_slug=status_slug)
        )


class RelationshipStatus(models.Model):
    id = SIDField(prefix='RS')
    name = models.CharField(_('name'), max_length=100)
    verb = models.CharField(_('verb'), max_length=100, unique=True)
    from_slug = models.CharField(_('from slug'), max_length=100,
        help_text=_("Denote the relationship from the user, i.e. 'following'"),
        unique=True)
    to_slug = models.CharField(_('to slug'), max_length=100,
        help_text=_("Denote the relationship to the user, i.e. 'followers'"),
        unique=True)
    symmetrical_slug = models.CharField(_('symmetrical slug'), max_length=100,
        help_text=_("When a mutual relationship exists, i.e. 'friends'"),
        unique=True)
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
    id = SIDField()
    from_user = models.ForeignKey(User,
        related_name='from_users', verbose_name=_('from user'))
    to_user = models.ForeignKey(User,
        related_name='to_users', verbose_name=_('to user'),
        null=True, blank=True)
    status = models.ForeignKey(RelationshipStatus, verbose_name=_('status'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    weight = models.FloatField(_('weight'), default=1.0, blank=True, null=True)
    site = models.ForeignKey(Site, default=settings.SITE_ID,
        verbose_name=_('site'), related_name='relationships')
    extra_data = jsonfield.JSONField(_('extra data'), default=None, blank=True,
                                     null=True, serialize=False)

    class Meta:
        unique_together = (('from_user', 'to_user', 'status', 'site'),)
        ordering = ('created',)
        verbose_name = _('Relationship')
        verbose_name_plural = _('Relationships')

    def __unicode__(self):
        return (_('Relationship from %(from_user)s to %(to_user)s')
                % {'from_user': self.from_user.username,
                   'to_user': self.to_user.username if self.to_user else 'None'})

    @staticmethod
    def get_owner_fields():
        return ('to_user', 'from_user')

    def is_owner(self, user):
        return user.pk in (self.to_user_id, self.from_user_id)


field = models.ManyToManyField(User, through=Relationship,
                               symmetrical=False, related_name='related_to')


class RelationshipManager(User._default_manager.__class__):
    def __init__(self, instance=None, *args, **kwargs):
        super(RelationshipManager, self).__init__(*args, **kwargs)
        self.instance = instance

    def add(self, user, status=None, symmetrical=False, extra_data=None):
        """
        Add a relationship from one user to another with the given status,
        which defaults to "following".

        Adding a relationship is by default asymmetrical (akin to following
        someone on twitter).  Specify a symmetrical relationship (akin to being
        friends on facebook) by passing in :param:`symmetrical` = True

        .. note::

            If :param:`symmetrical` is set, the function will return a tuple
            containing the two relationship objects created
        """
        if not status:
            status = RelationshipStatus.objects.following()

        try:
            relationship = Relationship.objects.get(
                from_user=self.instance,
                to_user=user,
                status=status,
                site=Site.objects.get_current(),
            )
        except Relationship.DoesNotExist:
            relationship = Relationship.objects.create(
                from_user=self.instance,
                to_user=user,
                status=status,
                site=Site.objects.get_current(),
                extra_data=extra_data
            )

        if symmetrical:
            return (relationship, user.relationships.add(self.instance, status, False, extra_data))
        else:
            return relationship

    def remove(self, user, status=None, symmetrical=False):
        """
        Remove a relationship from one user to another, with the same caveats
        and behavior as adding a relationship.
        """
        if not status:
            status = RelationshipStatus.objects.following()

        res = Relationship.objects.filter(
            from_user=self.instance,
            to_user=user,
            status=status,
            site__pk=settings.SITE_ID
        ).delete()

        if symmetrical:
            return (res, user.relationships.remove(self.instance, status, False))
        else:
            return res

    def _get_from_query(self, status):
        return dict(
            to_users__from_user=self.instance,
            to_users__status=status,
            to_users__site__pk=settings.SITE_ID,
        )

    def _get_to_query(self, status):
        return dict(
            from_users__to_user=self.instance,
            from_users__status=status,
            from_users__site__pk=settings.SITE_ID
        )

    def get_relationships(self, status, symmetrical=False):
        """
        Returns a QuerySet of user objects with which the given user has
        established a relationship.
        """
        query = self._get_from_query(status)

        if symmetrical:
            query.update(self._get_to_query(status))

        return User.objects.filter(**query)

    def get_related_to(self, status):
        """
        Returns a QuerySet of user objects which have created a relationship to
        the given user.
        """
        return User.objects.filter(**self._get_to_query(status))

    def only_to(self, status):
        """
        Returns a QuerySet of user objects who have created a relationship to
        the given user, but which the given user has not reciprocated
        """
        from_relationships = self.get_relationships(status)
        to_relationships = self.get_related_to(status)
        return to_relationships.exclude(pk__in=from_relationships.values_list('pk'))

    def only_from(self, status):
        """
        Like :method:`only_to`, returns user objects with whom the given user
        has created a relationship, but which have not reciprocated
        """
        from_relationships = self.get_relationships(status)
        to_relationships = self.get_related_to(status)
        return from_relationships.exclude(pk__in=to_relationships.values_list('pk'))

    def exists(self, user, status=None, symmetrical=False):
        """
        Returns boolean whether or not a relationship exists between the given
        users.  An optional :class:`RelationshipStatus` instance can be specified.
        """
        query = dict(
            to_users__from_user=self.instance,
            to_users__to_user=user,
            to_users__site__pk=settings.SITE_ID,
        )

        if status:
            query.update(to_users__status=status)

        if symmetrical:
            query.update(
                from_users__to_user=self.instance,
                from_users__from_user=user,
                from_users__site__pk=settings.SITE_ID
            )

            if status:
                query.update(from_users__status=status)

        return User.objects.filter(**query).exists()

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
        return self.get_relationships(RelationshipStatus.objects.following(), True)


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

elif django.VERSION > (1, 2) and django.VERSION < (1, 4):

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

else:

    fake_rel = ManyToManyRel(
        to=User,
        through=Relationship)

    RelatedManager = create_many_related_manager(RelationshipManager, fake_rel)

    class RelationshipsDescriptor(object):
        def __get__(self, instance, instance_type=None):
            manager = RelatedManager(
                model=User,
                query_field_name='related_to',
                instance=instance,
                symmetrical=False,
                source_field_name='from_user',
                target_field_name='to_user',
                through=Relationship,
            )
            return manager

#HACK
field.contribute_to_class(User, 'relationships')
setattr(User, 'relationships', RelationshipsDescriptor())
