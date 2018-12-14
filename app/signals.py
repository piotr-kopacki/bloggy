from .models import User, Entry, Notification, Tag
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

import re

@receiver(post_save, sender=Entry)
def entry_notification(sender, instance, created, **kwargs):
    """
    Signal used to create notification(s) when an entry is created
    This function notifies an user if this entry is a reply to him.
    This function notifies an user if he's mentioned (by @username) in one's entry
    """
    if created:
        # First find usernames mentioned (by @ tag)
        p = re.compile(r'^(@)(\w+)$')
        usernames = set([p.match(c).group(2) for c in instance.content.split() if p.match(c)])
        # Remove the author of an entry from users to notify
        if instance.user.username in usernames:
            usernames.remove(instance.user.username)
        # If entry has a parent and it's parent is not the same author then notify about a reply
        # and delete from usernames if being notified
        if instance.parent and instance.parent.user.username != instance.user.username:
            if instance.parent.user.username in usernames:
                usernames.remove(instance.parent.user.username)
            Notification.objects.create(type='user_replied', sender=instance.user, target=instance.parent.user, object=instance)
        # Notify mentioned users without the author of an entry
        for name in usernames:
            if name == instance.user.username:
                continue
            try:
                target = User.objects.get(username=name)
            except:
                continue
            Notification.objects.create(type='user_mentioned', sender=instance.user, target=target, object=instance)