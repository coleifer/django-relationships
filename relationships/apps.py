from django.apps import AppConfig


class RelationshipsConfig(AppConfig):
    name = 'relationships'

    def ready(self):
        from django.contrib.auth import get_user_model
    	User = get_user_model()