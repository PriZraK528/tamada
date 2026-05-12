from datetime import datetime, time

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Event, Registration
from .permissions import IsOrganizerOrReadOnly
from .serializers import EventSerializer, RegisterSerializer, RegistrationSerializer, UserBriefSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserBriefSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


def _parse_range_datetime(value: str):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is not None:
        return dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.get_current_timezone())
    d = parse_date(value)
    if d is not None:
        naive = datetime.combine(d, time.min)
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return None


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]

    def get_queryset(self):
        qs = Event.objects.annotate(registrations_count=Count("registrations")).select_related("organizer")
        user = self.request.user
        if user.is_authenticated:
            qs = qs.filter(Q(is_public=True) | Q(organizer=user))
        else:
            qs = qs.filter(is_public=True)

        from_param = self.request.query_params.get("from")
        to_param = self.request.query_params.get("to")
        dt_from = _parse_range_datetime(from_param) if from_param else None
        dt_to = _parse_range_datetime(to_param) if to_param else None
        if dt_from is not None:
            qs = qs.filter(starts_at__gte=dt_from)
        if dt_to is not None:
            qs = qs.filter(starts_at__lte=dt_to)
        return qs.order_by("starts_at", "id")

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="registrations")
    def registrations(self, request, pk=None):
        event = self.get_object()
        if event.organizer_id != request.user.id:
            raise PermissionDenied()
        qs = Registration.objects.filter(event=event).select_related("user")
        return Response(RegistrationSerializer(qs, many=True).data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated], url_path="register")
    def register(self, request, pk=None):
        event = self.get_object()
        if request.method == "POST":
            if event.organizer_id == request.user.id:
                raise ValidationError({"detail": "Нельзя записаться на своё событие."})
            if Registration.objects.filter(event=event, user=request.user).exists():
                raise ValidationError({"detail": "Вы уже записаны на это событие."})
            if event.capacity is not None:
                if Registration.objects.filter(event=event).count() >= event.capacity:
                    raise ValidationError({"detail": "Свободных мест больше нет."})
            comment = (request.data.get("comment") or "") if isinstance(request.data, dict) else ""
            reg = Registration.objects.create(event=event, user=request.user, comment=comment)
            return Response(RegistrationSerializer(reg).data, status=status.HTTP_201_CREATED)

        deleted, _ = Registration.objects.filter(event=event, user=request.user).delete()
        if not deleted:
            raise ValidationError({"detail": "Вы не были записаны на это событие."})
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeEventsList(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Event.objects.filter(organizer=self.request.user)
            .annotate(registrations_count=Count("registrations"))
            .select_related("organizer")
            .order_by("starts_at", "id")
        )


class MeRegistrationsList(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Registration.objects.filter(user=self.request.user)
            .select_related("event", "user")
            .order_by("-event__starts_at", "-id")
        )
