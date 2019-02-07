"""bloggy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from allauth.account.views import (
    LoginView,
    LogoutView,
    PasswordResetDoneView,
    PasswordResetFromKeyDoneView,
    PasswordResetFromKeyView,
    PasswordResetView,
    SignupView,
)
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import include, path

from .api import router

logged_users_redirect = user_passes_test(lambda u: u.is_anonymous, "/")

urlpatterns = [
    path("", include("app.urls")),
    path("api-v1/", include(router.urls)),
    path("api-auth/", include("rest_auth.urls")),
    path("api-auth/registration/", include("rest_auth.registration.urls")),
    # path("signup/", SignupView.as_view(), name="account_signup"),
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
    path("admin/", admin.site.urls),
]
