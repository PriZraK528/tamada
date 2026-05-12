from rest_framework import serializers

from .models import Event, Registration


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["id", "event", "name", "email", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        event = attrs.get("event")
        if not event:
            return attrs
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if not event.is_public and (not user or not user.is_authenticated):
            raise serializers.ValidationError("Событие недоступно для записи.")

        email = attrs.get("email")
        if email and Registration.objects.filter(event=event, email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Этот email уже зарегистрирован на событие."})

        if event.capacity is not None:
            current = Registration.objects.filter(event=event).count()
            if current >= event.capacity:
                raise serializers.ValidationError("Свободных мест больше нет.")
        return attrs


class EventSerializer(serializers.ModelSerializer):
    registrations_count = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        if self.instance:
            starts = attrs.get("starts_at", self.instance.starts_at)
            ends = attrs["ends_at"] if "ends_at" in attrs else self.instance.ends_at
        else:
            starts = attrs.get("starts_at")
            ends = attrs.get("ends_at")
        if ends and starts and ends < starts:
            raise serializers.ValidationError("Время окончания не может быть раньше начала.")
        return attrs

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
            "is_public",
            "created_at",
            "updated_at",
            "registrations_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "registrations_count"]

