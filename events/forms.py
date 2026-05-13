from datetime import datetime

from django import forms
from django.conf import settings
from django.utils import timezone

from .models import Event


def _combine_local_date_time(d, t):
    naive = datetime.combine(d, t)
    if settings.USE_TZ:
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return naive


def _local_date_time_parts(dt):
    if dt is None:
        return None, None
    if settings.USE_TZ and timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.date(), dt.time().replace(second=0, microsecond=0)


class EventForm(forms.ModelForm):
    """Форма создания и редактирования события."""

    VIS_PUBLIC = "public"
    VIS_PRIVATE = "private"

    starts_date = forms.DateField(
        label="Дата начала",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d", "%d.%m.%Y"],
    )
    starts_time = forms.TimeField(
        label="Время начала",
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": "60"}),
        input_formats=["%H:%M", "%H:%M:%S"],
    )
    ends_date = forms.DateField(
        label="Дата окончания",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d", "%d.%m.%Y"],
        help_text="Необязательно. Оставьте пустым вместе с временем окончания, если дата конца не нужна.",
    )
    ends_time = forms.TimeField(
        label="Время окончания",
        required=False,
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": "60"}),
        input_formats=["%H:%M", "%H:%M:%S"],
    )

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
        fields = ["title", "description", "location", "capacity"]
        labels = {
            "title": "Название",
            "description": "Описание",
            "location": "Место или формат",
            "capacity": "Максимум участников",
        }
        help_texts = {
            "title": "Коротко, чтобы было понятно, о чём событие.",
            "description": "Расскажите подробности: программа, что взять с собой, как связаться с организатором.",
            "location": "Адрес, название площадки или ссылка на онлайн-встречу (Zoom, Google Meet и т.п.).",
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
            "capacity": forms.NumberInput(attrs={"min": 1, "placeholder": "Без ограничения — оставьте пустым"}),
        }

    field_order = [
        "title",
        "description",
        "location",
        "starts_date",
        "starts_time",
        "ends_date",
        "ends_time",
        "capacity",
        "visibility",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            if self.instance.starts_at:
                d, t = _local_date_time_parts(self.instance.starts_at)
                self.initial["starts_date"] = d
                self.initial["starts_time"] = t
                self.fields["starts_date"].initial = d
                self.fields["starts_time"].initial = t
            if self.instance.ends_at:
                d, t = _local_date_time_parts(self.instance.ends_at)
                self.initial["ends_date"] = d
                self.initial["ends_time"] = t
                self.fields["ends_date"].initial = d
                self.fields["ends_time"].initial = t
            self.fields["visibility"].initial = (
                self.VIS_PUBLIC if self.instance.is_public else self.VIS_PRIVATE
            )

    def clean(self):
        cleaned = super().clean()
        sd = cleaned.get("starts_date")
        st = cleaned.get("starts_time")
        if not sd or not st:
            raise forms.ValidationError("Укажите дату и время начала события.")
        cleaned["starts_at"] = _combine_local_date_time(sd, st)

        ed = cleaned.get("ends_date")
        et = cleaned.get("ends_time")
        if ed and et:
            cleaned["ends_at"] = _combine_local_date_time(ed, et)
            if cleaned["ends_at"] < cleaned["starts_at"]:
                raise forms.ValidationError("Окончание не может быть раньше начала.")
        elif not ed and not et:
            cleaned["ends_at"] = None
        else:
            raise forms.ValidationError(
                "Для окончания заполните и дату, и время, либо оставьте оба поля окончания пустыми."
            )
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.starts_at = self.cleaned_data["starts_at"]
        obj.ends_at = self.cleaned_data["ends_at"]
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
