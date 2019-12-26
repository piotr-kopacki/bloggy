from django.contrib import admin

from .models import Entry, Tag


class EntryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user_formatted", "parent_formatted", "created_date")


admin.site.register(Entry, EntryAdmin)
admin.site.register(Tag)
