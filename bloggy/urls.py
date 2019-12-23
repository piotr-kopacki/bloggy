from django.contrib import admin
from django.urls import path, include

from .api import router

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("", include("app.urls")),
    path("api-v1/", include(router.urls)),
    path("api-auth/", include("rest_auth.urls")),
    path("api-auth/registration/", include("rest_auth.registration.urls")),
]
