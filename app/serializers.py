from rest_framework import serializers

from .models import Entry, User


class EntrySerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.pk")
    content = serializers.SerializerMethodField()
    content_formatted = serializers.SerializerMethodField()
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
            "parent",
            "upvotes",
            "downvotes",
            "user_upvoted",
            "user_downvoted",
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
        )

    def get_upvotes(self, obj):
        return obj.upvotes.count()

    def get_downvotes(self, obj):
        return obj.downvotes.count()

    def get_content(self, obj):
        return obj.content if not obj.deleted else "deleted"

    def get_content_formatted(self, obj):
        return obj.content_formatted if not obj.deleted else "deleted"

    def get_user_upvoted(self, obj):
        u = self.context.get("request").user
        return obj.upvotes.filter(pk=u.pk).exists()

    def get_user_downvoted(self, obj):
        u = self.context.get("request").user
        return obj.downvotes.filter(pk=u.pk).exists()
