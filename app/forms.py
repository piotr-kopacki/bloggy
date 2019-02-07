from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data['username'].lower()
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', 'A user with that username already exists.')
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.display_name = self.cleaned_data["username"]
        user.username = self.cleaned_data["username"].lower()
        if commit:
            user.save()
        return user
