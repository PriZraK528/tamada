from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Event, Registration

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["username", "password", "password_confirm", "email", "first_name", "last_name"]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})
        return attrs

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class RegistrationSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ["id", "event", "user", "comment", "created_at"]
        read_only_fields = ["id", "event", "user", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    registrations_count = serializers.IntegerField(read_only=True)
    organizer = UserBriefSerializer(read_only=True)

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
            "organizer",
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
        read_only_fields = ["id", "organizer", "created_at", "updated_at", "registrations_count"]
