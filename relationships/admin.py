from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as DefaultUserModel

from .compat import User
from .forms import RelationshipStatusAdminForm
from .models import Relationship, RelationshipStatus


class RelationshipInline(admin.TabularInline):
    model = Relationship
    raw_id_fields = ('from_user', 'to_user')
    extra = 1
    fk_name = 'from_user'


class UserRelationshipAdminMixin(object):
    inlines = (RelationshipInline,)


class RelationshipStatusAdmin(admin.ModelAdmin):
    form = RelationshipStatusAdminForm


if User == DefaultUserModel:
    class UserRelationshipAdmin(UserRelationshipAdminMixin, UserAdmin):
        pass

    admin.site.unregister(User)
    admin.site.register(User, UserRelationshipAdmin)

admin.site.register(RelationshipStatus, RelationshipStatusAdmin)
