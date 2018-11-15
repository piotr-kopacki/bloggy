from django.urls import path

from .views import EntryDetailView, UserDetailView, UserRankingView, home, hot, signup, top

urlpatterns = [
    path("", home, name="home"),
    path("top/", top, name="top"),
    path("hot/", hot, name="hot"),
    path("ranking/", UserRankingView.as_view(), name="ranking"),
    path("entry/<int:pk>", EntryDetailView.as_view(), name="entry-detail-view"),
    path("users/signup/", signup, name="signup"),
    path("users/<int:pk>", UserDetailView.as_view(), name="user-detail-view"),
]
