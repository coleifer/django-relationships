from django import template
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.template import TemplateSyntaxError
from django.utils.functional import wraps
from relationships.models import RelationshipStatus
from relationships.utils import positive_filter, negative_filter

register = template.Library()


class IfRelationshipNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false, *args):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.from_user, self.to_user, self.status = args
        self.status = self.status.replace('"', '')  # strip quotes

    def render(self, context):
        from_user = template.resolve_variable(self.from_user, context)
        to_user = template.resolve_variable(self.to_user, context)

        if from_user.is_anonymous() or to_user.is_anonymous():
            return self.nodelist_false.render(context)

        try:
            status = RelationshipStatus.objects.by_slug(self.status)
        except RelationshipStatus.DoesNotExist:
            raise template.TemplateSyntaxError('RelationshipStatus not found')

        if status.from_slug == self.status:
            val = from_user.relationships.exists(to_user, status)
        elif status.to_slug == self.status:
            val = to_user.relationships.exists(from_user, status)
        else:
            val = from_user.relationships.exists(to_user, status, symmetrical=True)

        if val:
            return self.nodelist_true.render(context)

        return self.nodelist_false.render(context)


@register.tag
def if_relationship(parser, token):
    """
    Determine if a certain type of relationship exists between two users.
    The ``status`` parameter must be a slug matching either the from_slug,
    to_slug or symmetrical_slug of a RelationshipStatus.

    Example::

        {% if_relationship from_user to_user "friends" %}
            Here are pictures of me drinking alcohol
        {% else %}
            Sorry coworkers
        {% endif_relationship %}

        {% if_relationship from_user to_user "blocking" %}
            damn seo experts
        {% endif_relationship %}
    """
    bits = list(token.split_contents())
    if len(bits) != 4:
        raise TemplateSyntaxError, "%r takes 3 arguments:\n%s" % \
            (bits[0], if_relationship.__doc__)
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfRelationshipNode(nodelist_true, nodelist_false, *bits[1:])


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
