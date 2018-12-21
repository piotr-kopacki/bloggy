import bleach
import markdown
import re
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from mptt.models import MPTTModel, TreeForeignKey


class User(AbstractUser):
    """
    Custom user model to use in the future.
    Email is required to create an User.
    """

    email = models.EmailField(null=False, unique=True, blank=False)

    EMAIL_FIELD = "email"

    @cached_property
    def points(self):
        """
        Returns user points by a formula count_of_entries + upvotes_from_entries - downvotes_from_entries
        """
        user_entries = Entry.objects.filter(user=self.pk)
        aggregations = user_entries.aggregate(models.Count('upvotes'), models.Count('downvotes'))
        return user_entries.count() + aggregations['upvotes__count'] - aggregations['downvotes__count']

    @cached_property
    def notifications_unread_count(self):
        return Notification.objects.filter(target=self).filter(read=False).count()
    
    @cached_property
    def notifications(self):
        return Notification.objects.filter(target=self)[:5]



class Tag(models.Model):
    """
    Generic tag class

    ::name         - name of the tag (primary key)
    ::author       - tag may have an author who can moderate the tag
    ::observers    - list of users who observe the tag
    ::blacklisters - list of users who blacklisted the tag
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.TextField(max_length=255, primary_key=True)
    observers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="observers", blank=True
    )
    blacklisters = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="blacklisters", blank=True
    )


    def __str__(self):
        return "#" + self.name


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
    modified_date = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag)

    class MPTTMeta:
        order_insertion_by = ["-created_date"]

    class Meta:
        verbose_name_plural = "Entries"

    def __str__(self):
        if len(self.content) > 45:
            return f'"{self.content:.45}..."'
        return f'"{self.content}"'

    def get_absolute_url(self):
        return reverse('entry-detail-view', args=[str(self.id)])

    def format_content(self):
        # Convert 'h1' (#) tag into a hyperlink to a tag
        self.content_formatted = self.content
        p = re.compile(r"(\W|^)(#)([a-zA-Z]+\b)(?![a-zA-Z_#])")
        self.content_formatted = re.sub(
            p,
            lambda m: '{}<a href="{}">#{}</a>'.format(
                m.group(1),
                reverse("tag", kwargs={"tag": m.group(3).lower()}),
                m.group(3).lower(),
            ),
            self.content_formatted,
        )
        # Convert @user tag into a hyperlink to a profile
        p = re.compile(r"(\W|^)(@)([a-zA-Z0-9]+\b)(?![a-zA-Z0-9_#])")
        self.content_formatted = re.sub(
            p, r'\1<a href="/users/\3">@\3</a>', self.content_formatted
        )
        # Clean and format content
        self.content_formatted = bleach.clean(
            markdown.markdown(self.content_formatted, extensions=["extra"]),
            settings.MARKDOWN_TAGS,
            settings.MARKDOWN_ATTRS,
        )
        self.content = bleach.clean(
            self.content, settings.MARKDOWN_TAGS, settings.MARKDOWN_ATTRS
        )

    def save(self, *args, **kwargs):
        """
        Custom save method:
        - Adds tags to self.tags field
        - Notifies tag observers about new entry
        - Formats and cleans content
        """
        created = True if not self.pk else False
        # If entry is being modified, update the modified date field
        if not created:
            self.modified_date = timezone.now()
        # Format the content before saving
        self.format_content()
        # Call save before accessing tags field to avoid errors
        super().save(*args, **kwargs)
        # Clear tags so if user deletes a tag from content it won't appear.
        self.tags.clear()
        tags_to_add = [Tag.objects.get_or_create(name=tag_name)[0] for tag_name in self.get_tags]
        self.tags.add(*tags_to_add)

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

    @cached_property
    def votes_sum(self):
        """
        Returns substract of downvotes from upvotes
        """
        return self.upvotes.count() - self.downvotes.count()

    @cached_property
    def root_pk(self):
        """
        Returns id of root node (if node is a root node then root_pk = self.pk)
        """
        return self.get_root().pk

    @cached_property
    def has_children(self):
        """
        Returns True if entry has children nodes
        """
        return self.get_children().exists()

    @cached_property
    def get_tags(self):
        """
        Returns list of tag names in content of entry
        """
        p = r"(\W|^)(#)([a-zA-Z]+\b)(?![a-zA-Z_#])"
        return list(set([f[2].lower() for f in re.findall(p, self.content)]))


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
