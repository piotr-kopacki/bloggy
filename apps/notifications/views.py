from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 25
    template_name = "notifications/notifications.html"
    login_url = reverse_lazy("account_login")
    context_object_name = "notifications_paginated"

    def get_queryset(self):
        return Notification.objects.filter(target=self.request.user)
