from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from entries.models import Entry
from .models import User
from .forms import UserCreationForm


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class EntryInLine(admin.TabularInline):
    model = Entry
    extra = 0


class CustomUserAdmin(UserAdmin):
    add_form = UserCreateForm
    inlines = [EntryInLine]
    fieldsets = (
        (None, {'fields': ('username', 'display_name', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'classes': ('collapse',), 'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'classes': ('collapse',), 'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(User, CustomUserAdmin)
