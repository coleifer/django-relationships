from django import template
from django.urls import reverse

try:
    from django.db.models.loading import get_model
except ImportError:
    from django.apps import apps

    get_model = apps.get_model

from django.template import TemplateSyntaxError
from django.utils.functional import wraps
from django.utils.translation import ugettext as _

from relationships.models import RelationshipStatus
from relationships.utils import (
    positive_filter,
    negative_filter
)

register = template.Library()


@register.simple_tag
def relationship(from_user, to_user, status):
    """
    Determine if a certain type of relationship exists between two users.
    The ``status`` parameter must be a slug matching either the from_slug,
    to_slug or symmetrical_slug of a RelationshipStatus.

    Example::
        {% relationship from_user to_user "friends" as felas %}
        {% relationship from_user to_user "blocking" as blocked %}
        {% if felas %}
            Here are pictures of me drinking alcohol
        {% elif blocked %}
            damn seo experts
        {% else %}
            Sorry coworkers
        {% endif %}
    """
    requested_status = status.replace('"', '')  # strip quotes

    if from_user.is_anonymous() or to_user.is_anonymous():
        return False

    try:
        status = RelationshipStatus.objects.by_slug(requested_status)
    except RelationshipStatus.DoesNotExist:
        raise template.TemplateSyntaxError('RelationshipStatus not found')

    if status.from_slug == requested_status:
        val = from_user.relationships.exists(to_user, status)
    elif status.to_slug == requested_status:
        val = to_user.relationships.exists(from_user, status)
    else:
        val = from_user.relationships.exists(to_user, status, symmetrical=True)

    if val:
        return True

    return False


@register.filter
def add_relationship_url(user, status):
    """
    Generate a url for adding a relationship on a given user.  ``user`` is a
    User object, and ``status`` is either a relationship_status object or a
    string denoting a RelationshipStatus

    Usage::

        href="{{ user|add_relationship_url:"following" }}"
    """
    if isinstance(status, RelationshipStatus):
        status = status.from_slug
    return reverse('relationship_add', args=[user.username, status])


@register.filter
def remove_relationship_url(user, status):
    """
    Generate a url for removing a relationship on a given user.  ``user`` is a
    User object, and ``status`` is either a relationship_status object or a
    string denoting a RelationshipStatus

    Usage::

        href="{{ user|remove_relationship_url:"following" }}"
    """
    if isinstance(status, RelationshipStatus):
        status = status.from_slug
    return reverse('relationship_remove', args=[user.username, status])


def positive_filter_decorator(func):
    def inner(qs, user):
        if isinstance(qs, basestring):
            model = get_model(*qs.split('.'))
            if not model:
                return []
            qs = model._default_manager.all()
        if user.is_anonymous():
            return qs.none()
        return func(qs, user)

    inner._decorated_function = getattr(func, '_decorated_function', func)
    return wraps(func)(inner)


def negative_filter_decorator(func):
    def inner(qs, user):
        if isinstance(qs, basestring):
            model = get_model(*qs.split('.'))
            if not model:
                return []
            qs = model._default_manager.all()
        if user.is_anonymous():
            return qs
        return func(qs, user)

    inner._decorated_function = getattr(func, '_decorated_function', func)
    return wraps(func)(inner)


@register.filter
@positive_filter_decorator
def friend_content(qs, user):
    return positive_filter(qs, user.relationships.friends())


@register.filter
@positive_filter_decorator
def following_content(qs, user):
    return positive_filter(qs, user.relationships.following())


@register.filter
@positive_filter_decorator
def followers_content(qs, user):
    return positive_filter(qs, user.relationships.followers())


@register.filter
@negative_filter_decorator
def unblocked_content(qs, user):
    return negative_filter(qs, user.relationships.blocking())
