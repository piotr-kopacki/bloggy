from django.contrib.auth.decorators import user_passes_test
from django.urls import path

from .views import UserRankingView, UserDetailView, SignUpView

logged_users_redirect = user_passes_test(lambda u: u.is_anonymous, "/")

urlpatterns = [
    path("ranking/", UserRankingView.as_view(), name="ranking"),
    path("users/<str:username>/", UserDetailView.as_view(), name="user-detail-view"),
    path("signup/", logged_users_redirect(SignUpView.as_view()), name="account_signup"),
]
