from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class UserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
