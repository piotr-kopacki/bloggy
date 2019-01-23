import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Entry, Notification, PrivateMessage, Tag, User


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 25
    template_name = "app/notifications.html"
    login_url = reverse_lazy("account_login")
    context_object_name = "notifications_paginated"

    def get_queryset(self):
        return Notification.objects.filter(target=self.request.user)


class PrivateMessageView(LoginRequiredMixin, View):
    template_name = "app/private_messages.html"
    login_url = reverse_lazy("account_login")

    def get(self, request, target=None):
        """
        This view returns 2 possible results depending on whether user is looking at his inbox
        or is looking at a conversation with other user.
        """
        template_name = self.template_name
        context = {}
        if target and target != self.request.user.username:
            target = get_object_or_404(User, username=target)
            PrivateMessage.objects.filter(Q(target=self.request.user) & Q(author=target)).update(read=True, read_date=timezone.now())
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
            template_name = "app/inbox.html"
            unread_private_messages = (
                PrivateMessage.objects.filter(Q(target=self.request.user))
                .values("author__username")
                .annotate(unread=Count("read", filter=Q(read=False)))
            )
            all_private_messages = list(
                PrivateMessage.objects.filter(author=self.request.user)
                .values("target__username")
                .distinct()
            )
            to_add = []
            for unread_pm in unread_private_messages:
                for pm in all_private_messages:
                    if pm["target__username"] == unread_pm["author__username"]:
                        pm["unread"] = unread_pm["unread"]
                        break
                else:
                    to_add.append(
                        {
                            "target__username": unread_pm["author__username"],
                            "unread": unread_pm["unread"],
                        }
                    )
            context["all_conversations"] = sorted(
                all_private_messages + to_add, key=lambda p: p["target__username"]
            )
        return render(request, template_name, context)


class UserRankingView(ListView):
    """
    Simple ranking view
    """

    model = User
    paginate_by = 10
    template_name = "app/ranking.html"

    def get_queryset(self):
        return sorted(User.objects.all(), key=lambda u: u.points, reverse=True)


class EntryDetailView(DetailView):
    """
    This view returns a queryset consiting of:
    - Parent entry (if exists)
    - Selected entry
    - Child entries (if exist)
    as 'entries'
    """

    model = Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = []
        entry = super().get_object()
        if entry.parent:
            queryset.append(entry.parent)
        for e in entry.get_descendants(include_self=True):
            queryset.append(e)
        context["entries"] = queryset
        return context


class UserDetailView(DetailView):
    model = User
    context_object_name = "user_profile"

    def get_object(self, queryset=None):
        """
        Overridden to enable searching by username
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        username = self.kwargs.get("username")
        if not username:
            return super().get_object(queryset)
        queryset = queryset.filter(username=username)
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj

    def get_context_data(self, **kwargs):
        """
        Shows only 5 last discussions user participated in
        """
        context = super().get_context_data(**kwargs)
        user_entries = Entry.objects.filter(user=self.get_object().pk)
        last_discussions = []
        added_entries = 0
        for entry in user_entries:
            if added_entries == 5:
                break
            # Skip entries which are already in the list
            elif any([entry.pk == discussion.pk for discussion in last_discussions]):
                continue
            else:
                added_entries += 1
            for node in list(entry.get_family()):
                last_discussions.append(node)
        context["entries"] = last_discussions
        return context


class HomeView(View):
    """
    Home (front page) view.
    """
    def filter_roots_by_tag(self, root_nodes, tag_name):
        if tag_name:
            if re.search(r"^([a-zA-Z]+)$", tag_name):
                tag_name = tag_name.lower()
                tag_object, _ = Tag.objects.get_or_create(name=tag_name)
                return (root_nodes.filter(tags__name=tag_object.name), tag_object)
        return (root_nodes, None)

    def sort_roots(self, root_nodes, sorting):
        # If entries are sorted by hotness, filter entries from last 6 hours
        # Also annotate 'hotness' by a simple formula (count of upvotes + count of downvotes + 0.5 * count of children)
        if sorting == "hot":
            root_nodes = (
                root_nodes.filter(created_date__gte=timezone.now() - timedelta(hours=6))
                .annotate(
                    hotness=(
                        (Count("upvotes") + Count("downvotes")) + (0.5 * Count("children"))
                    )
                )
                .order_by("-hotness")
            )
        # Top sorting sorts descending by subtracting root's downvotes from upvotes
        elif sorting == "top":
            root_nodes = root_nodes.annotate(
                overall_votes=(Count("upvotes") - Count("downvotes"))
            ).order_by("-overall_votes")
        return root_nodes

    def filter_roots_by_blacklist(self, request, root_nodes):
        return root_nodes.exclude(
                Q(tags__blacklisters=request.user) & ~Q(user=request.user)
            )

    def rebuild_tree(self, request, root_nodes):
        # To make pagination possible we need to paginate root nodes only.
        # Then we need to replace default object_list in the paginator queryset
        # with a new quryset with rebuilt trees
        paginator = Paginator(root_nodes, settings.PAGINATE_ENTRIES_BY)
        page = request.GET.get("page")
        queryset = []
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        new_queryset = []
        for node in queryset.object_list:
            new_queryset.append(node)
            for descendant in node.get_descendants():
                # Hide entries with level higher or equal to 9
                # and mark parents that they have hidden children
                if descendant.level >= 9:
                    if descendant.level == 9:
                        new_queryset[-1].has_hidden_children = True
                    continue
                new_queryset.append(descendant)
        queryset.object_list = new_queryset
        return queryset

    def get(self, request, sorting=None, tag=None):
        root_nodes = Entry.objects.root_nodes()
        tag_object = None
        root_nodes, tag_object = self.filter_roots_by_tag(root_nodes, tag)
        root_nodes = self.sort_roots(root_nodes, sorting)
        if not tag and request.user.is_authenticated:
            root_nodes = self.filter_roots_by_blacklist(request, root_nodes)
        queryset = self.rebuild_tree(request, root_nodes)
        return render(
            request, "app/home.html", {"entries": queryset, "browsed_tag": tag_object}
        )
