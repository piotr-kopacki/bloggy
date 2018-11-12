from django.urls import path

from .views import home, top, hot, signup, EntryDetailView, UserDetailView

urlpatterns = [
    path('', home, name='home'),
    path('top/', top, name='top'),
    path('hot/', hot, name='hot'),
    path('users/signup/', signup, name='signup'),
    path('entry/<int:pk>', EntryDetailView.as_view(), name='entry-detail-view'),
    path('users/<int:pk>', UserDetailView.as_view(), name='user-detail-view'),
]
