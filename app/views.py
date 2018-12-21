from datetime import timedelta

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from mptt.utils import get_cached_trees

from .models import Entry, User, Notification, Tag

import re
import time


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 25
    template_name = "app/notifications.html"
    login_url = reverse_lazy("account_login")
    context_object_name = "notifications_paginated"

    def get_queryset(self):
        return Notification.objects.filter(target=self.request.user)


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


def HomeView(request, sorting=None, tag=None):
    """
    Home (front page) view.
    It accepts one keyword parameter 'sorting' which is passed from 'hot' and 'top' views.
    To sort a TreeModel from django-mptt this function first sorts root nodes and then
    rebuilds the trees using get_descendants method on every root.
    """
    root_nodes = Entry.objects.root_nodes()
    tag_object = None
    if tag:
        if re.search(r"^([a-zA-Z]+)$", tag):
            tag = tag.lower()
            tag_object, _ = Tag.objects.get_or_create(name=tag)
            root_nodes = root_nodes.filter(tags__name=tag_object.name)
    # If entries are sorted by hotness, filter entries from last 6 hours
    # Also annotate 'hotness' by a simple formula (count of upvotes + count of downvotes + 0,5 * count of children)
    if sorting == "hot":
        root_nodes = (
            root_nodes.filter(created_date__gte=timezone.now() - timedelta(hours=6))
            .annotate(
                hotness=(
                    (Count("upvotes") + Count("downvotes")) * 0.5 + Count("children")
                )
            )
            .order_by("-hotness")
        )
    # Top sorting sorts descending by subtracting root's downvotes from upvotes
    elif sorting == "top":
        root_nodes = root_nodes.annotate(
            overall_votes=(Count("upvotes") - Count("downvotes"))
        ).order_by("-overall_votes")
    # Filter root nodes by blacklisted tags
    if not tag and request.user.is_authenticated:
        root_nodes = root_nodes.exclude(Q(tags__blacklisters=request.user) & ~Q(user=request.user))
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
    return render(
        request, "app/home.html", {"entries": queryset, "browsed_tag": tag_object}
    )

