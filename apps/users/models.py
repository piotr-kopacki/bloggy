from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.functional import cached_property

from entries.models import Entry
from messeges.models import PrivateMessage
from notifications.models import Notification


class User(AbstractUser):
    """
    Custom user model to use in the future.
    Email is required to create an User.
    """

    email = models.EmailField(null=False, unique=True, blank=False)
    display_name = models.CharField(max_length=150, null=False, blank=True)

    EMAIL_FIELD = "email"

    @cached_property
    def points(self):
        """
        Returns user points by a formula count_of_entries + upvotes_from_entries - downvotes_from_entries
        """
        user_entries = Entry.objects.filter(user=self.pk)
        aggregations = user_entries.aggregate(
            models.Count("upvotes"), models.Count("downvotes")
        )
        return (
            user_entries.count()
            + aggregations["upvotes__count"]
            - aggregations["downvotes__count"]
        )

    @cached_property
    def notifications_unread_count(self):
        return Notification.objects.filter(target=self).filter(read=False).count()

    @cached_property
    def notifications(self):
        return Notification.objects.filter(target=self).order_by("-id")[:5]

    @cached_property
    def private_messages_unread_count(self):
        return PrivateMessage.objects.filter(target=self).filter(read=False).count()
