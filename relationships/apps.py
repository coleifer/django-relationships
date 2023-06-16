from django.apps import AppConfig


class RelationshipsConfig(AppConfig):
    name = 'relationships'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        from relationships import compat
        compat.User = User

        from relationships import models as rmodels
        rmodels.User = User

        from django.db.models import ManyToManyField
        from relationships.models import (
            RelationshipsDescriptor,
            Relationship
        )
        field = ManyToManyField(
            User,
            through=Relationship,
            symmetrical=False,
            related_name='related_to'
        )
        field.contribute_to_class(User, 'relationships')
        setattr(User, 'relationships', RelationshipsDescriptor())
