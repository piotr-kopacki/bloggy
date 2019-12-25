from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    """
    Generic notification class

    ::type    - describes the type of notification to be later used in templates
    ::sender  - user who is responsible for making the notification
    ::object  - context object
    ::target  - target user who will be notified
    ::content - text to display (optional)
    ::read    - logic if notification has been read
    """

    type = models.CharField(
        max_length=100,
        help_text="Used to determine type of notification e.g. user_mentioned or user_replied",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender"
    )
    object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey("object_content_type", "object_id")
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="target"
    )
    content = models.TextField(blank=True, null=True)
    read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]
