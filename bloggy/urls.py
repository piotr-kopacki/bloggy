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
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from .api import router

logged_users_redirect = user_passes_test(lambda u: u.is_anonymous, '/')

urlpatterns = [
    path('', include('app.urls')),
    path('api-v1/', include(router.urls)),
    path('api-auth/', include('rest_auth.urls')),
    path('api-auth/registration/', include('rest_auth.registration.urls')),
    path('users/login/', logged_users_redirect(auth_views.LoginView.as_view()), name='login'),
    path('users/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('users/password_reset/', logged_users_redirect(auth_views.PasswordResetView.as_view()), name='password_reset'),
    path('users/password_reset/done/', logged_users_redirect(auth_views.PasswordResetDoneView.as_view()), name='password_reset_done'),
    path('users/reset/<uidb64>/<token>/', logged_users_redirect(auth_views.PasswordResetConfirmView.as_view()), name='password_reset_confirm'),
    path('users/reset/done/', logged_users_redirect(auth_views.PasswordResetCompleteView.as_view()), name='password_reset_complete'),
    path('admin/', admin.site.urls),
]
