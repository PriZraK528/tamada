from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import EventViewSet, MeEventsList, MeRegistrationsList

router = DefaultRouter()
router.register("events", EventViewSet, basename="event")

urlpatterns = [
    path("me/events/", MeEventsList.as_view(), name="api-me-events"),
    path("me/registrations/", MeRegistrationsList.as_view(), name="api-me-registrations"),
] + router.urls
