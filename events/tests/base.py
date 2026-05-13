from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from events.models import Event

User = get_user_model()


def user(username="user1", email="user1@test.com", password="testpass123"):
    return User.objects.create_user(username=username, email=email, password=password)


def event(organizer, title="Событие", is_public=True, capacity=None, **kwargs):
    data = {
        "organizer": organizer,
        "title": title,
        "description": "",
        "location": "",
        "starts_at": timezone.now() + timedelta(days=1),
        "ends_at": None,
        "capacity": capacity,
        "is_public": is_public,
    }
    data.update(kwargs)
    return Event.objects.create(**data)
