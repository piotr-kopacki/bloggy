from django.contrib.auth import get_user_model
from rest_framework import serializers

from entries.models import Tag, Entry
from messeges.models import PrivateMessage
from notifications.models import Notification


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    observers = serializers.SerializerMethodField()
    user_observes = serializers.SerializerMethodField()
    user_blacklisted = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        read_only_fields = ("author", "name")
        fields = ("name", "author", "observers", "user_observes", "user_blacklisted")

    def get_observers(self, obj):
        return obj.observers.all().count()

    def get_user_observes(self, obj):
        u = self.context.get("request").user
        return obj.observers.filter(pk=u.pk).exists()

    def get_user_blacklisted(self, obj):
        u = self.context.get("request").user
        return obj.blacklisters.filter(pk=u.pk).exists()


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.username")
    object = serializers.ReadOnlyField(source="object_id")
    target = serializers.ReadOnlyField(source="target.username")

    class Meta:
        model = Notification
        read_only_fields = (
            "id",
            "sender",
            "read",
            "type",
            "object",
            "target",
            "created_date",
            "content",
        )
        fields = (
            "id",
            "sender",
            "type",
            "object",
            "content",
            "target",
            "created_date",
            "read",
        )

    def validate_read(self, value):
        if value is not True:
            raise serializers.ValidationError("Cannot unread notifications")
        return value


class PrivateMessageSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    target = serializers.CharField()
    read = serializers.SerializerMethodField()
    read_date = serializers.SerializerMethodField()

    def get_read(self, obj):
        """
        If user is an author of a private message, the 'read' field should always
        show True - because obviously he has seen the message he has created.
        """
        u = self.context.get("request").user
        if u == obj.author:
            return True
        return obj.read

    def get_read_date(self, obj):
        """
        If user is an author of a private message, the 'read_date' field should show
        date of creation - because user sees his messages the moment he creates it ;)
        """
        u = self.context.get("request").user
        if u == obj.author:
            return obj.created_date
        return obj.read_date

    class Meta:
        model = PrivateMessage
        fields = ("id", "author", "text", "target", "created_date", "read_date", "read")
        read_only_fields = ("id", "author", "created_date", "read_date", "read")


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    upvotes = serializers.SerializerMethodField()
    downvotes = serializers.SerializerMethodField()
    user_upvoted = serializers.SerializerMethodField()
    user_downvoted = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        read_only_fields = (
            "id",
            "content_formatted",
            "created_date",
            "user",
            "upvotes",
            "downvotes",
            "user_upvoted",
            "user_downvoted",
            "deleted",
            "tags",
        )
        fields = (
            "id",
            "content",
            "content_formatted",
            "created_date",
            "user",
            "parent",
            "upvotes",
            "downvotes",
            "user_upvoted",
            "user_downvoted",
            "deleted",
            "tags",
        )
        extra_kwargs = {"tags": {"view_name": "tags-detail"}}

    def validate_parent(self, value):
        if self.instance:
            if self.instance.parent and value:
                raise serializers.ValidationError(
                    "Cannot change already assigned parent!"
                )
        return value

    def get_upvotes(self, obj):
        return obj.upvotes.count()

    def get_downvotes(self, obj):
        return obj.downvotes.count()

    def get_user_upvoted(self, obj):
        u = self.context.get("request").user
        return obj.upvotes.filter(pk=u.pk).exists()

    def get_user_downvoted(self, obj):
        u = self.context.get("request").user
        return obj.downvotes.filter(pk=u.pk).exists()
