from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View

from .models import PrivateMessage


User = get_user_model()


class PrivateMessageView(LoginRequiredMixin, View):
    template_name = "messages/private_messages.html"
    login_url = reverse_lazy("account_login")

    def get(self, request, target=None):
        """
        This view returns 2 possible results depending on whether user is looking at his inbox
        or is looking at a conversation with other user.
        """
        template_name = self.template_name
        context = {}
        if target:
            target = target.lower()
        if target and target != self.request.user.username:
            target = get_object_or_404(User, username=target)
            PrivateMessage.objects.filter(
                Q(target=self.request.user) & Q(author=target)
            ).update(read=True, read_date=timezone.now())
            context["conversation"] = PrivateMessage.objects.filter(
                (Q(target=self.request.user) & Q(author=target))
                | (Q(target=target) & Q(author=self.request.user))
            ).order_by("created_date")

            context["conversation_with"] = target.username
        else:
            """
            There is a lot of hackery going here - mainly because of poorly implemented model of private message.
            Firstly, I fetch all messages to user, group them by author and count the unread ones.
            Then I fetch all the messages from user to others and combine the results of the first query with it (unread count)
            """
            template_name = "messages/inbox.html"
            unread_private_messages = (
                PrivateMessage.objects.filter(Q(target=self.request.user))
                .values("author__display_name")
                .annotate(unread=Count("read", filter=Q(read=False)))
            )
            all_private_messages = list(
                PrivateMessage.objects.filter(author=self.request.user)
                .values("target__display_name")
                .distinct()
            )
            to_add = []
            for unread_pm in unread_private_messages:
                for pm in all_private_messages:
                    if pm["target__display_name"] == unread_pm["author__display_name"]:
                        pm["unread"] = unread_pm["unread"]
                        break
                else:
                    to_add.append(
                        {
                            "target__display_name": unread_pm["author__display_name"],
                            "unread": unread_pm["unread"],
                        }
                    )
            context["all_conversations"] = sorted(
                all_private_messages + to_add, key=lambda p: p["target__display_name"]
            )
        return render(request, template_name, context)
