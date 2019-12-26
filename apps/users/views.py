from django.contrib.auth import authenticate, login
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView, DetailView

from entries.models import Entry
from .models import User
from .forms import SignUpForm


class SignUpView(View):
    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            user = authenticate(
                username=new_user.username, password=form.cleaned_data.get("password1")
            )
            login(request, user)
            return redirect("home")
        return render(request, "account/signup.html", {"form": form})

    def get(self, request):
        form = SignUpForm()
        return render(request, "account/signup.html", {"form": form})


class UserRankingView(ListView):
    """
    Simple ranking view
    """

    model = User
    paginate_by = 10
    template_name = "users/ranking.html"

    def get_queryset(self):
        return sorted(User.objects.all(), key=lambda u: u.points, reverse=True)


class UserDetailView(DetailView):
    model = User
    context_object_name = "user_profile"
    template_name = 'users/user_detail.html'

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
        else:
            username = username.lower()
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
