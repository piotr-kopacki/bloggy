from django.urls import path

from .views import EntryDetailView, HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("top/", HomeView.as_view(), {"sorting": "top"}, name="top"),
    path("hot/", HomeView.as_view(), {"sorting": "hot"}, name="hot"),
    path("entries/tag/<str:tag>/", HomeView.as_view(), name="tag"),
    path("entries/<int:pk>/", EntryDetailView.as_view(), name="entry-detail-view"),
]
