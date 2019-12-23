from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Entry, Notification, PrivateMessage, Tag, User
from .forms import UserChangeForm, UserCreationForm


class EntryInLine(admin.TabularInline):
    model = Entry
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [EntryInLine]
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'bio', 'photo')}),
        ('Permissions', {'classes': ('collapse',), 'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'classes': ('collapse',), 'fields': ('last_login', 'date_joined')}),
    )


class EntryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user_formatted", "parent_formatted", "created_date")

admin.site.register(Entry, EntryAdmin)
admin.site.register(Notification)
admin.site.register(Tag)
admin.site.register(PrivateMessage)
