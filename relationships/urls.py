from django.conf.urls.defaults import *

urlpatterns = patterns('relationships.views',
    url(r'^(?P<username>[\w-]+)/(?:(?P<status_slug>[\w-]+)/)?$', 'relationship_list', name='relationship_list'),
    url(r'^add/(?P<username>[\w-]+)/(?P<status_slug>[\w-]+)/$', 'relationship_handler', {'add': True}, name='relationship_add'),
    url(r'^remove/(?P<username>[\w-]+)/(?P<status_slug>[\w-]+)/$', 'relationship_handler', {'add': False}, name='relationship_remove'),
)
