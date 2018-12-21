from .models import User, Entry, Notification, Tag
from django.db.models.signals import post_save, m2m_changed
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


@receiver(m2m_changed, sender=Entry.tags.through)
def entry_tag_notification(sender, instance, pk_set, action, **kwargs):
    if not instance.modified_date and "post" in action:
        already_notified = set()
        reversed_user = reverse(
                "user-detail-view", kwargs={"username": instance.user.username}
            )
        reversed_entry = reverse(
            "entry-detail-view", kwargs={"pk": instance.pk}
        )
        for tag in instance.tags.all():
            for observer in tag.observers.all():
                if observer.username == instance.user.username or observer in already_notified:
                    continue
                reversed_tag = reverse("tag", kwargs={"tag": tag.name})
                content = (
                    f'<a href="{reversed_user}">{instance.user.username}</a> used tag <a href="{reversed_tag}">#{tag.name}</a>'
                    f' in <a href="{reversed_entry}">"{instance.content:.25}..."</a>'
                )
                n = Notification.objects.create(
                    type="tag_used",
                    sender=instance.user,
                    target=observer,
                    object=instance,
                    content=content,
                )
                already_notified.add(observer)