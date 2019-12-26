import bleach

from django.conf import settings
from django.db import models


class PrivateMessage(models.Model):
    """
    Class for a private message model. It is very similiar to a notification model.
    ::author - user who sent a message
    ::text   - content of a message
    ::target - target user who recieved the message
    ::read   - true if user has read the message
    ::created_date - datetime when message was sent by author
    ::read_date    - datetime when message was read by target
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pms_sent")
    text = models.CharField(max_length=500)
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pms_received"
    )
    read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    read_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.text = bleach.clean(self.text, tags=[], attributes=[])
        super().save(*args, **kwargs)
