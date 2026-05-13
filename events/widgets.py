from django import forms
from django.conf import settings
from django.utils import timezone


class DateTimeLocalInput(forms.DateTimeInput):
    """Значение для input type=\"datetime-local\" (без сдвига при редактировании)."""

    input_type = "datetime-local"

    def __init__(self, attrs=None, format=None):
        attrs = attrs or {}
        attrs.setdefault("step", "60")
        super().__init__(attrs=attrs, format=format or "%Y-%m-%dT%H:%M")

    def format_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if settings.USE_TZ and timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%dT%H:%M")
