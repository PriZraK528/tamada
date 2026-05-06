from rest_framework import serializers

from .models import Event, Registration


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ["id", "event", "name", "email", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    registrations_count = serializers.IntegerField(read_only=True)

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

