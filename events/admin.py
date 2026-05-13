from django.contrib import admin

from .models import Event, Invitation, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    autocomplete_fields = ("user",)


class InvitationInline(admin.TabularInline):
    model = Invitation
    extra = 0
    readonly_fields = ("token", "created_at")
    fields = ("email", "status", "token", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "starts_at", "location", "capacity", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("title", "location", "description", "organizer__username")
    date_hierarchy = "starts_at"
    autocomplete_fields = ("organizer",)
    inlines = [RegistrationInline, InvitationInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "event", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("email", "event__title", "token")
    autocomplete_fields = ("event",)
    readonly_fields = ("token", "created_at")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("user__username", "user__email", "event__title")
    autocomplete_fields = ("user", "event")
