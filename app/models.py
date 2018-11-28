import bleach
import markdown
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from mptt.models import MPTTModel, TreeForeignKey


class Notification(models.Model):
    """
    Generic notification class

    ::type   - describes the type of notification to be later used in templates
    ::sender - user who is responsible for making the notification
    ::object - context object
    ::target - target user who will be notified
    ::read   - logic if notification has been read
    """
    type = models.CharField(max_length=100, help_text="Used to determine type of notification e.g. user_mentioned or user_replied")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')
    object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_content_type', 'object_id')
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='target')
    read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']


class User(AbstractUser):
    """
    Custom user model to use in the future.
    Email is required to create an User.
    """
    email = models.EmailField(null=False, unique=True, blank=False)

    EMAIL_FIELD = "email"

    @property
    def points(self):
        """
        Returns user points by a formula count_of_entries + upvotes_from_entries
        """
        user_entries = Entry.objects.filter(user=self.pk)
        return user_entries.count() + sum(
            [entry.upvotes.count() for entry in user_entries]
        )


class Entry(MPTTModel):
    """
    Model for a blog entry.
    ::user              - author of an entry
    ::parent            - parent entry (None if is root)
    ::content           - nonformatted content but cleaned with bleach
    ::content_formatted - cleaned and formatted with markdown content
    ::upvotes           - stores users who upvoted an Entry
    ::downvotes         - stores user who downvoted an Entry
    ::created_date      - date of creation
    ::deleted           - true if entry is marked as deleted
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
    content_formatted = models.TextField(default="")
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="upvotes"
    )
    downvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="downvotes"
    )
    created_date = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)

    class MPTTMeta:
        order_insertion_by = ["-created_date"]

    def __str__(self):
        if not self.parent:
            return f'"{self.content:.20}..."'
        return f'"{self.content:.20}..."'

    def save(self, *args, **kwargs):
        """
        Cleans content from dirty tags and saves formatted (markdowned) content into content_formatted field.
        """
        self.content_formatted = bleach.clean(markdown.markdown(self.content, extensions=["extra"]), settings.MARKDOWN_TAGS, settings.MARKDOWN_ATTRS)
        self.content = bleach.clean(
            self.content, settings.MARKDOWN_TAGS, settings.MARKDOWN_ATTRS
        )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        On delete mark the entry as deleted, don't delete from db.
        """
        # Delete notifications related to an entry
        Notification.objects.filter(object_id=self.pk).delete()
        if self.has_children:
            self.deleted = True
            self.save()
        else:
            super().delete(*args, **kwargs)
    
    @property
    def votes_sum(self):
        """
        Returns substract of downvotes from upvotes
        """
        return self.upvotes.count() - self.downvotes.count()

    @property
    def root_pk(self):
        """
        Returns id of root node (if node is a root node then root_pk = self.pk)
        """
        return self.get_root().pk

    @property
    def has_children(self):
        """
        True if entry has children nodes
        """
        return self.get_children().exists()

    def parent_formatted(self):
        """
        Formats parent node into a hyperlink
        """
        if not self.parent:
            return "-"
        url = reverse("admin:app_entry_change", args=(self.parent.pk,))
        return format_html('<a href="{}">#{}</a>', url, self.parent.pk)

    def user_formatted(self):
        """
        Formats author into a hyperlink
        """
        url = reverse("admin:app_user_change", args=(self.user.pk,))
        return format_html('<a href="{}">{}</a>', url, self.user.username)

    parent_formatted.short_description = "Parent entry"
    user_formatted.short_description = "User"
