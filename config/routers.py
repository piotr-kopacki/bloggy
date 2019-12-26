from rest_framework import routers

from api.views import (
    EntryViewSet,
    NotificationViewSet,
    PrivateMessageViewSet,
    TagViewSet,
)

router = routers.DefaultRouter()
router.register(r"entries", EntryViewSet)
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"privatemessages", PrivateMessageViewSet, basename="privatemessages")
router.register(r"tags", TagViewSet, basename="tags")
