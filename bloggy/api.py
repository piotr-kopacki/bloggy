from rest_framework import routers

from app.apiviews import EntryViewSet, VoteViewSet, NotificationViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r"entries", EntryViewSet)
router.register(r"vote", VoteViewSet, basename="vote")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"tags", TagViewSet, basename="tags")
