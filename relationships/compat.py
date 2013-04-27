import django


# Django 1.5 add support for custom auth user model
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    try:
        from django.contrib.auth.models import User
    except ImportError:
        raise ImportError(u"User model is not to be found.")

# location of patterns, url, include changes in 1.4 onwards
try:
    from django.conf.urls import patterns, url, include
except:
    from django.conf.urls.defaults import patterns, url, include
