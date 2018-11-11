from django.urls import path

from .views import home, top, hot, signup

urlpatterns = [
    path('', home, name='home'),
    path('top/', top, name='top'),
    path('hot/', hot, name='hot'),
    path('users/signup/', signup, name='signup'),
]
