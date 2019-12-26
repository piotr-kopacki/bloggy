import re
from datetime import timedelta

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic.detail import DetailView

from .models import Entry, Tag


class EntryDetailView(DetailView):
    """
    This view returns a queryset consiting of:
    - Parent entry (if exists)
    - Selected entry
    - Child entries (if exist)
    as 'entries'
    """

    model = Entry
    template_name = 'entries/entry_detail.html'

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
                        (Count("upvotes") + Count("downvotes"))
                        + (0.5 * Count("children"))
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
            request, "entries/home.html", {"entries": queryset, "browsed_tag": tag_object}
        )
