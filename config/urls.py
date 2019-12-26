from allauth.account.views import (
    LoginView,
    LogoutView,
    PasswordResetDoneView,
    PasswordResetFromKeyDoneView,
    PasswordResetFromKeyView,
    PasswordResetView,
)
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import include, path

from .routers import router

logged_users_redirect = user_passes_test(lambda u: u.is_anonymous, "/")

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api-auth/", include("rest_auth.urls")),
    path("api-auth/registration/", include("rest_auth.registration.urls")),

    path("login/", logged_users_redirect(LoginView.as_view()), name="account_login"),
    path("logout/", LogoutView.as_view(), name="account_logout"),
    path(
        "password/reset/",
        logged_users_redirect(PasswordResetView.as_view()),
        name="account_reset_password",
    ),
    url(
        r"^users/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        logged_users_redirect(PasswordResetFromKeyView.as_view()),
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        logged_users_redirect(PasswordResetFromKeyDoneView.as_view()),
        name="account_reset_password_from_key_done",
    ),
    path(
        "password/reset/done/",
        logged_users_redirect(PasswordResetDoneView.as_view()),
        name="account_reset_password_done",
    ),

    path("", include("entries.urls")),
    path("inbox/", include("messeges.urls")),
    path("notifications/", include("notifications.urls")),
    path("", include("users.urls")),

    path("api-v1/", include(router.urls)),
]
