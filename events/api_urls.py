from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import EventViewSet, InvitationViewSet, MeEventsList, MeRegistrationsList

router = DefaultRouter()
router.register("events", EventViewSet, basename="event")
router.register("invitations", InvitationViewSet, basename="invitation")

urlpatterns = [
    path("me/events/", MeEventsList.as_view(), name="api-me-events"),
    path("me/registrations/", MeRegistrationsList.as_view(), name="api-me-registrations"),
] + router.urls
