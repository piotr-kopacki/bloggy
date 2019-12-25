from django.urls import path

from .views import PrivateMessageView

urlpatterns = [
    path("", PrivateMessageView.as_view(), name="inbox"),
    path(
        "user/<str:target>/", PrivateMessageView.as_view(), name="inbox-user-view"
    ),
]
