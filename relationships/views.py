import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import ListView

from .decorators import require_user
from .models import RelationshipStatus


@login_required
def relationship_redirect(request):
    return HttpResponseRedirect(reverse('relationship_list', args=[request.user.username]))


def _relationship_list(request, queryset, template_name=None, *args, **kwargs):
    return ListView.as_view(
        queryset=queryset,
        template_name=template_name,
        paginate_by=20,
        context_object_name='relationship_list'
    )(request, page=int(request.GET.get('page', 0)), *args, **kwargs)


def get_relationship_status_or_404(status_slug):
    try:
        return RelationshipStatus.objects.by_slug(status_slug)
    except RelationshipStatus.DoesNotExist:
        raise Http404


@require_user
def relationship_list(request, user, status_slug=None,
                      template_name='relationships/relationship_list.html'):
    if not status_slug:
        status = RelationshipStatus.objects.following()
        status_slug = status.from_slug
    else:
        # get the relationship status object we're talking about
        status = get_relationship_status_or_404(status_slug)

    # do some basic authentication
    if status.login_required and not request.user.is_authenticated():
        path = urlquote(request.get_full_path())
        tup = settings.LOGIN_URL, 'next', path
        return HttpResponseRedirect('%s?%s=%s' % tup)

    if status.private and not request.user == user:
        raise Http404

    # get a queryset of users described by this relationship
    if status.from_slug == status_slug:
        qs = user.relationships.get_relationships(status=status)
    elif status.to_slug == status_slug:
        qs = user.relationships.get_related_to(status=status)
    else:
        qs = user.relationships.get_relationships(status=status, symmetrical=True)

    ec = dict(
        from_user=user,
        status=status,
        status_slug=status_slug,
    )

    return _relationship_list(request, qs, template_name, extra_context=ec)


@login_required
@require_user
def relationship_handler(request, user, status_slug, add=True,
                         template_name='relationships/confirm.html',
                         success_template_name='relationships/success.html'):

    status = get_relationship_status_or_404(status_slug)
    is_symm = status_slug == status.symmetrical_slug

    if request.method == 'POST':
        if add:
            request.user.relationships.add(user, status, is_symm)
        else:
            request.user.relationships.remove(user, status, is_symm)

        if request.is_ajax():
            response = {'result': '1'}
            return HttpResponse(json.dumps(response), mimetype="application/json")

        if request.GET.get('next'):
            return HttpResponseRedirect(request.GET['next'])

        template_name = success_template_name

    return render(request,
        template_name,
        {'to_user': user, 'status': status, 'add': add})
