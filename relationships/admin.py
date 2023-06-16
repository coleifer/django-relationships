from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as DefaultUserModel

from relationships.compat import User
from relationships.forms import RelationshipStatusAdminForm
from relationships.models import (
    Relationship,
    RelationshipStatus
)


class RelationshipInline(admin.TabularInline):
    model = Relationship
    raw_id_fields = ['from_user', 'to_user']
    extra = 1
    fk_name = 'from_user'


class UserRelationshipAdminMixin(object):
    inlines = [RelationshipInline, ]


class RelationshipStatusAdmin(admin.ModelAdmin):
    form = RelationshipStatusAdminForm

    list_display = ['name', 'verb', 'from_slug', 'to_slug', 'symmetrical_slug']


if User == DefaultUserModel:
    class UserRelationshipAdmin(UserRelationshipAdminMixin, UserAdmin):
        pass


    try:
        admin.site.unregister(User)
    except admin.sites.NotRegistered:
        pass
    admin.site.register(User, UserRelationshipAdmin)

admin.site.register(RelationshipStatus, RelationshipStatusAdmin)
