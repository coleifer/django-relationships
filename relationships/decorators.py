from django.shortcuts import get_object_or_404

from .compat import User


def require_user(view):
    def inner(request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
        return view(request, user, *args, **kwargs)
    return inner
