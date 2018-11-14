from rest_framework import serializers
from .models import Entry, User


class EntrySerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.pk")

    class Meta:
        model = Entry
        fields = (
            "id",
            "content",
            "content_formatted",
            "created_date",
            "user",
            "parent",
            "upvotes",
            "downvotes",
        )
