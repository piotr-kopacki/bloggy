from django.contrib.auth import login, authenticate
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect
from django.db.models import Count
from django.utils import timezone

from .models import Entry
from .forms import SignUpForm

from mptt.utils import get_cached_trees
from datetime import timedelta


class RootView(DetailView):
    model = Entry
    queryset = Entry.objects.root_nodes()

    def get_context_data(self, **kwargs):
        root_nodes = self.Entry.objects.root_nodes()


def home(request, sorting='new'):
    if sorting == 'new':
        root_nodes = Entry.objects.root_nodes()
    elif sorting == 'hot':
        root_nodes = Entry.objects.root_nodes().filter(date__gte=timezone.now()-timedelta(hours=6)).annotate(
            hotness=(Count('upvotes') +
                        Count('downvotes') + Count('children'))
        ).order_by('-hotness')
    elif sorting == 'top':
        root_nodes = Entry.objects.root_nodes().annotate(overall_votes=(
            Count('upvotes') - Count('downvotes'))).order_by('-overall_votes')
    paginator = Paginator(root_nodes, 25)
    page = request.GET.get('page')
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
        new_queryset.extend(node.get_descendants())
    queryset.object_list = new_queryset
    if request.user.is_authenticated:
        for entry in queryset:
            if entry.upvotes.filter(pk=request.user.id).exists():
                entry.style_class = 'user-upvoted'
            elif entry.downvotes.filter(pk=request.user.id).exists():
                entry.style_class = 'user-downvoted'
            elif entry.votes_sum == 0:
                entry.style_class = 'neutral'
            elif entry.votes_sum > 0:
                entry.style_class = 'positive'
            else:
                entry.style_class = 'negative'

    return render(request, 'app/base.html', {'entries': queryset})


def top(request):
    return home(request, 'top')


def hot(request):
    return home(request, 'hot')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
