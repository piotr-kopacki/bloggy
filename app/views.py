from datetime import timedelta

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from mptt.utils import get_cached_trees

from .forms import SignUpForm
from .models import Entry, User, Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 25
    template_name = "app/notifications.html"
    login_url = reverse_lazy('account_login')
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

    def get_context_data(self, **kwargs):
        """
        Shows only 5 last discussions user participated in
        """
        context = super().get_context_data(**kwargs)
        user_entries = Entry.objects.filter(user=super().get_object().pk)
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
        context["user"].entries = last_discussions
        context["user"].entries_count = user_entries.count()
        return context


def home(request, sorting="new"):
    """
    Home (front page) view.
    It accepts one keyword parameter 'sorting' which is passed from 'hot' and 'top' views.
    To sort a TreeModel from django-mptt this function first sorts root nodes and then
    rebuilds the trees using get_descendants method on every root.
    """
    import time
    now = time.time()
    if sorting == "new":
        root_nodes = Entry.objects.root_nodes()
    # If entries are sorted by hotness, filter entries from last 6 hours
    # Also annotate 'hotness' by a simple formula (count of upvotes + count of downvotes + 0,5 * count of children)
    elif sorting == "hot":
        root_nodes = (
            Entry.objects.root_nodes()
            .filter(created_date__gte=timezone.now() - timedelta(hours=6))
            .annotate(
                hotness=(
                    (Count("upvotes") + Count("downvotes")) * 0.5 + Count("children")
                )
            )
            .order_by("-hotness")
        )
    # Top sorting sorts descending by subtracting root's downvotes from upvotes
    elif sorting == "top":  
        root_nodes = (
            Entry.objects.root_nodes()
            .annotate(overall_votes=(Count("upvotes") - Count("downvotes")))
            .order_by("-overall_votes")
        )
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
    # Adds context to an entry if it was upvoted or downvoted
    if request.user.is_authenticated:
        for entry in queryset:
            if entry.upvotes.filter(pk=request.user.id).exists():
                entry.style_class = "user-upvoted"
            elif entry.downvotes.filter(pk=request.user.id).exists():
                entry.style_class = "user-downvoted"
            elif entry.votes_sum == 0:
                entry.style_class = "neutral"
    return render(request, "app/base.html", {"entries": queryset})


def top(request):
    return home(request, "top")

def hot(request):
    return home(request, "hot")
