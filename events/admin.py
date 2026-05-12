from django.contrib import admin

from .models import Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "starts_at", "location", "capacity", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("title", "location", "description", "organizer__username")
    date_hierarchy = "starts_at"
    autocomplete_fields = ("organizer",)
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("user__username", "user__email", "event__title")
    autocomplete_fields = ("user", "event")
