from .models import User, Entry, Notification
from django.db.models.signals import post_save
from django.dispatch import receiver

import re

@receiver(post_save, sender=Entry)
def notify_reply_or_mentioned_user(sender, instance, created, **kwargs):
    """
    Signal to notify users when they are mentioned in an entry (only when it's created)
    or when someone replied to it's entry.
    """
    if created:
        p = re.compile(r'^@\w+$')
        usernames = set([p.match(c).group()[1:] for c in instance.content.split() if p.match(c)])
        # Create user_replied notification if entry has parent
        # and delete from usernames the parent user not to notify him
        # with user_mentioned notify
        if instance.parent and instance.parent.user.username != instance.user.username:
            if instance.parent.user.username in usernames:
                usernames.remove(instance.parent.user.username)
            Notification.objects.create(type='user_replied',sender=instance.user, target=instance.parent.user, object=instance)
        for name in usernames:
            # Don't notify author of an entry to disable notifying itself
            if name == instance.user.username:
                continue
            try:
                target = User.objects.get(username=name)
            except:
                continue
            Notification.objects.create(type='user_mentioned', sender=instance.user, target=target, object=instance)
            