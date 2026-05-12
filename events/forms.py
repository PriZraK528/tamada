from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "location", "starts_at", "ends_at", "capacity", "is_public"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Название"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Описание"}),
            "location": forms.TextInput(attrs={"placeholder": "Место или ссылка"}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "capacity": forms.NumberInput(attrs={"min": 1, "placeholder": "Без лимита — оставьте пустым"}),
        }
        help_texts = {
            "starts_at": "Удобнее выбрать дату и время встроенным календарём браузера.",
            "ends_at": "Необязательно.",
            "capacity": "Пусто — без ограничения по числу участников.",
            "is_public": "Если выключено, карточку видите только вы (и список «Мои»).",
        }

    def clean(self):
        cleaned = super().clean()
        starts = cleaned.get("starts_at")
        ends = cleaned.get("ends_at")
        if starts and ends and ends < starts:
            raise forms.ValidationError("Время окончания не может быть раньше начала.")
        return cleaned


class RegistrationCommentForm(forms.Form):
    comment = forms.CharField(
        required=False,
        label="Комментарий",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Необязательно"}),
    )
