from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.urls import reverse
from .models import User, Entry

class UserCreateForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'email',)

class EntryInLine(admin.TabularInline):
    model = Entry
    extra = 0

class CustomUserAdmin(UserAdmin):
    add_form = UserCreateForm
    inlines = [EntryInLine,]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', ),
        }),
    )

class EntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user_formatted', 'parent_formatted', 'created_date')

    



admin.site.register(User, CustomUserAdmin)
admin.site.register(Entry, EntryAdmin)