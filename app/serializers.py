from rest_framework import serializers

from .models import Entry, User, Notification

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.pk")
    object = serializers.ReadOnlyField(source="object_id")
    target = serializers.ReadOnlyField(source="target.pk")

    class Meta:
        model = Notification
        read_only_fields = (
            "id",
            "sender",
            "type",
            "object",
            "target",
            "created_date",
        )
        fields = (
            "id",
            "sender",
            "type",
            "object",
            "target",
            "created_date",
            "read",
        )
    
    def validate_read(self, value):
        if value == False:
            raise serializers.ValidationError("Cannot unread notifications")
        return value


class EntrySerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.pk")
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
            'deleted',
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
            'deleted',
        )

    def validate_parent(self, value):
        if self.instance:
            if self.instance.parent and value:
                raise serializers.ValidationError("Cannot change already assigned parent!")
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
