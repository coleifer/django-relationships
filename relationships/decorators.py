from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

def require_user(view):
    def inner(request, username, *args, **kwargs):
        user = get_object_or_404(User, username=username)
        return view(request, user, *args, **kwargs)
    return inner
