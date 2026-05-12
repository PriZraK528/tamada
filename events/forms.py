from django import forms

from .models import Registration


class RegistrationForm(forms.ModelForm):
    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    class Meta:
        model = Registration
        fields = ["name", "email", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Имя", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "email"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Комментарий (необязательно)"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not self.event or not email:
            return email
        if Registration.objects.filter(event=self.event, email__iexact=email).exists():
            raise forms.ValidationError("Этот email уже зарегистрирован на это событие.")
        return email

    def clean(self):
        cleaned = super().clean()
        if not self.event:
            return cleaned
        if self.event.capacity is not None:
            n = self.event.registrations.count()
            if n >= self.event.capacity:
                raise forms.ValidationError("Свободных мест больше нет.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.event = self.event
        if commit:
            obj.save()
        return obj
