from rest_framework import routers

from app.apiviews import EntryViewSet, VoteViewSet

router = routers.DefaultRouter()
router.register(r"entries", EntryViewSet)
router.register(r"vote", VoteViewSet, basename="vote")
