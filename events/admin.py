from django.contrib import admin

from .models import Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "location", "capacity", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("title", "location", "description")
    date_hierarchy = "starts_at"
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("email", "name", "event__title")
