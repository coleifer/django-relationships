from django.db.models import signals

from .models import RelationshipStatus, Relationship


def mutually_exclusive_fix(sender, instance, created, **kwargs):
    # instance will be the new relationship that was created
    # and since some applications will want to use the default
    # "following" and "blocking" statuses in tandem, this hook
    # handles deleting a "following" status when a "blocking" is
    # added, and vice-versa
    try:
        following = RelationshipStatus.objects.following()
        blocking = RelationshipStatus.objects.blocking()
    except RelationshipStatus.DoesNotExist:
        pass
    else:
        # check to see if the new status is "following" or "blocking"
        other = None
        if instance.status == following:
            other = blocking
        elif instance.status == blocking:
            other = following

        if other:
            # delete any status that may conflict with the new one
            Relationship.objects.filter(
                from_user=instance.from_user,
                to_user=instance.to_user,
                site=instance.site,
                status=other
            ).delete()


DISPATCH_UID = 'relationships.listeners.exclusive_fix'


def attach_relationship_listener(func=mutually_exclusive_fix, dispatch_uid=DISPATCH_UID):
    signals.post_save.connect(func, sender=Relationship, dispatch_uid=dispatch_uid)


def detach_relationship_listener(dispatch_uid=DISPATCH_UID):
    signals.post_save.disconnect(sender=Relationship, dispatch_uid=dispatch_uid)
