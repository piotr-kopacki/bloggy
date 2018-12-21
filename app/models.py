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

    @property
    def points(self):
        """
        Returns user points by a formula count_of_entries + upvotes_from_entries
        """
        user_entries = Entry.objects.filter(user=self.pk)
        return user_entries.count() + sum(
            [entry.upvotes.count() for entry in user_entries]
        )

    @cached_property
    def notifications_unread_count(self):
        return Notification.objects.filter(target=self).filter(read=False).count()



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
    deleted = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)

    class MPTTMeta:
        order_insertion_by = ["-created_date"]

    def __str__(self):
        if not self.parent:
            return f'"{self.content:.20}..."'
        return f'"{self.content:.20}..."'

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
        self.format_content()
        # Call save before accessing tags field to avoid errors
        super().save(*args, **kwargs)
        # Clear tags so if user deletes a tag from content it won't appear.
        self.tags.clear()
        for tag_name in self.get_tags:
            try:
                tag = Tag.objects.get(name=tag_name)
            except:
                tag = Tag.objects.create(name=tag_name)
            self.tags.add(tag)
        # Notify tag observers if tag is used (only when entry is a root)
        # Q: Why here and not in signals?
        # A: It's just Django limitation (probably not). We need to save the object first before accessing tag field
        #    (because it's ManyToManyField and Django doesn't allow manipulating it before it's saved in DB)
        #    and because of that the instance that signal gets has empty tag field.
        #    If we tried saving again then instance wouldn't be flagged as 'created'
        #    so that would enable users to create notifications by just editing content
        #    of an Entry and we don't want to do that.
        if created and not self.parent:
            for tag in self.tags.all():
                for observer in tag.observers.all():
                    if observer.username == self.user.username:
                        continue
                    reversed_user = reverse(
                        "user-detail-view", kwargs={"username": self.user.username}
                    )
                    reversed_entry = reverse(
                        "entry-detail-view", kwargs={"pk": self.pk}
                    )
                    reversed_tag = reverse("tag", kwargs={"tag": tag.name})
                    content = (
                        f'<a href="{reversed_user}">{self.user.username}</a> used tag <a href="{reversed_tag}">#{tag.name}</a>'
                        f' in <a href="{reversed_entry}">"{self.content_formatted:.25}..."</a>'
                    )
                    Notification.objects.create(
                        type="tag_used",
                        sender=self.user,
                        target=observer,
                        object=self,
                        content=content,
                    )

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
        Returns True if entry has children nodes
        """
        return self.get_children().exists()

    @property
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
