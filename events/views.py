from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistrationForm
from .models import Event


def event_list(request):
    events = (
        Event.objects.filter(is_public=True)
        .annotate(registrations_count=Count("registrations"))
        .order_by("starts_at", "id")
    )
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, pk):
    event = get_object_or_404(
        Event.objects.filter(is_public=True).annotate(registrations_count=Count("registrations")),
        pk=pk,
    )
    if request.method == "POST":
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Вы успешно записались на событие.")
                return redirect("event_detail", pk=event.pk)
            except IntegrityError:
                messages.error(request, "Этот email уже зарегистрирован на это событие.")
    else:
        form = RegistrationForm(event=event)
    return render(request, "events/event_detail.html", {"event": event, "form": form})
