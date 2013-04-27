from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .compat import User
from .forms import RelationshipStatusAdminForm
from .models import Relationship, RelationshipStatus


class RelationshipInline(admin.TabularInline):
    model = Relationship
    raw_id_fields = ('from_user', 'to_user')
    extra = 1
    fk_name = 'from_user'


class UserRelationshipAdmin(UserAdmin):
    inlines = (RelationshipInline,)


class RelationshipStatusAdmin(admin.ModelAdmin):
    form = RelationshipStatusAdminForm

admin.site.unregister(User)
admin.site.register(User, UserRelationshipAdmin)
admin.site.register(RelationshipStatus, RelationshipStatusAdmin)
