from django import forms

from .models import Event
from .widgets import DateTimeLocalInput

_DATETIME_LOCAL_FORMATS = [
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
]


class EventForm(forms.ModelForm):
    """Форма создания и редактирования события."""

    VIS_PUBLIC = "public"
    VIS_PRIVATE = "private"

    visibility = forms.ChoiceField(
        label="Видимость в каталоге",
        choices=[
            (
                VIS_PUBLIC,
                "Публичное — показывается на главной странице, зайти может любой пользователь",
            ),
            (
                VIS_PRIVATE,
                "Личное — в общем списке не отображается; открыть карточку могут вы и те, кого вы пригласили по ссылке",
            ),
        ],
        initial=VIS_PUBLIC,
        widget=forms.RadioSelect(),
        help_text="Публичные события проще находить. Личные удобны для закрытых встреч.",
    )

    class Meta:
        model = Event
        fields = ["title", "description", "location", "starts_at", "ends_at", "capacity"]
        labels = {
            "title": "Название",
            "description": "Описание",
            "location": "Место или формат",
            "starts_at": "Когда начинается",
            "ends_at": "Когда заканчивается",
            "capacity": "Максимум участников",
        }
        help_texts = {
            "title": "Коротко, чтобы было понятно, о чём событие.",
            "description": "Расскажите подробности: программа, что взять с собой, как связаться с организатором.",
            "location": "Адрес, название площадки или ссылка на онлайн-встречу (Zoom, Google Meet и т.п.).",
            "starts_at": "Дата и время начала. Удобнее выбрать встроенным календарём браузера.",
            "ends_at": "Необязательно. Укажите, если известно время окончания.",
            "capacity": "Оставьте пустым, если число гостей не ограничено.",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Например: Лекция по Django",
                    "autocomplete": "off",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "О чём встреча, для кого она, что важно знать участникам…",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "placeholder": "Аудитория 301, ул. Примерная, 1 или ссылка на видеозвонок",
                    "autocomplete": "street-address",
                }
            ),
            "starts_at": DateTimeLocalInput(),
            "ends_at": DateTimeLocalInput(),
            "capacity": forms.NumberInput(attrs={"min": 1, "placeholder": "Без ограничения — оставьте пустым"}),
        }

    field_order = [
        "title",
        "description",
        "location",
        "starts_at",
        "ends_at",
        "capacity",
        "visibility",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("starts_at", "ends_at"):
            self.fields[name].input_formats = _DATETIME_LOCAL_FORMATS + list(
                self.fields[name].input_formats or []
            )
        if self.instance.pk:
            self.fields["visibility"].initial = (
                self.VIS_PUBLIC if self.instance.is_public else self.VIS_PRIVATE
            )

    def clean(self):
        cleaned = super().clean()
        starts = cleaned.get("starts_at")
        ends = cleaned.get("ends_at")
        if starts and ends and ends < starts:
            raise forms.ValidationError("Время окончания не может быть раньше времени начала.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.is_public = self.cleaned_data["visibility"] == self.VIS_PUBLIC
        if commit:
            obj.save()
        return obj


class RegistrationCommentForm(forms.Form):
    comment = forms.CharField(
        required=False,
        label="Комментарий",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Необязательно"}),
    )
