from rest_framework.routers import DefaultRouter

from .api import EventViewSet, RegistrationViewSet

router = DefaultRouter()
router.register("events", EventViewSet, basename="event")
router.register("registrations", RegistrationViewSet, basename="registration")

urlpatterns = router.urls
