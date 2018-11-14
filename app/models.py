from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings
from django.urls import reverse

from mptt.models import MPTTModel, TreeForeignKey

import markdown
import bleach


class User(AbstractUser):
    email = models.EmailField(null=False, unique=True, blank=False)

    EMAIL_FIELD = "email"

    @property
    def points(self):
        user_entries = Entry.objects.filter(user=self.pk)
        return user_entries.count() + sum(
            [entry.upvotes.count() for entry in user_entries]
        )


class Entry(MPTTModel):
    """
    Model for a blog entry.

    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="author"
    )
    parent = TreeForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    content = models.TextField(
        max_length=4000, default="", help_text="Enter your thoughts here..."
    )
    content_formatted = models.TextField(max_length=4000, default="")
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="upvotes"
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="downvotes"
    )
    created_date = models.DateTimeField(default=timezone.now)

    class MPTTMeta:
        order_insertion_by = ["-created_date"]

    def __str__(self):
        if not self.parent:
            return f'"{self.content:.20}..."'
        return f'"{self.content:.20}..."'

    def save(self, *args, **kwargs):
        # Save raw content only when new content is provided so it doesn't save html tags
        self.content = bleach.clean(
            self.content, settings.MARKDOWN_TAGS, settings.MARKDOWN_ATTRS
        )
        self.content_formatted = bleach.clean(
            markdown.markdown(self.content, extensions=["extra"]),
            settings.MARKDOWN_TAGS,
            settings.MARKDOWN_ATTRS,
        )
        super().save(*args, **kwargs)

    @property
    def votes_sum(self):
        return self.upvotes.count() - self.downvotes.count()

    def parent_formatted(self):
        if not self.parent:
            return "-"
        url = reverse("admin:app_entry_change", args=(self.parent.pk,))
        return format_html('<a href="{}">#{}</a>', url, self.parent.pk)

    parent_formatted.short_description = "Parent entry"

    def user_formatted(self):
        url = reverse("admin:app_user_change", args=(self.user.pk,))
        return format_html('<a href="{}">{}</a>', url, self.user.username)

    user_formatted.short_description = "User"
