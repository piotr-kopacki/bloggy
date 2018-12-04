from django.urls import path

from .views import EntryDetailView, UserDetailView, UserRankingView, NotificationListView, home, hot, top

urlpatterns = [
    path("", home, name="home"),
    path("top/", top, name="top"),
    path("hot/", hot, name="hot"),
    path("ranking/", UserRankingView.as_view(), name="ranking"),
    path("entry/<int:pk>", EntryDetailView.as_view(), name="entry-detail-view"),
    path("notifications/", NotificationListView.as_view(), name="notifications-all"),
    path("users/<int:pk>", UserDetailView.as_view(), name="user-detail-view"),
]
