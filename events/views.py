from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventForm, RegistrationCommentForm
from .models import Event, Registration
from .serializers import RegisterSerializer


def signup(request):
    if request.user.is_authenticated:
        return redirect("event_list")
    submitted = request.method == "POST"
    serializer = RegisterSerializer(data=request.POST) if submitted else RegisterSerializer()
    if submitted and serializer.is_valid():
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Регистрация выполнена. Вы вошли в систему.")
        return redirect("event_list")
    return render(
        request,
        "registration/signup.html",
        {"serializer": serializer, "submitted": submitted},
    )


def event_list(request):
    events = (
        Event.objects.filter(is_public=True)
        .annotate(registrations_count=Count("registrations"))
        .select_related("organizer")
        .order_by("starts_at", "id")
    )
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, pk):
    base_qs = Event.objects.annotate(registrations_count=Count("registrations")).select_related("organizer")
    if request.user.is_authenticated:
        event = get_object_or_404(
            base_qs.filter(Q(is_public=True) | Q(organizer=request.user)),
            pk=pk,
        )
    else:
        event = get_object_or_404(base_qs.filter(is_public=True), pk=pk)

    registered = False
    if request.user.is_authenticated:
        registered = Registration.objects.filter(event=event, user=request.user).exists()

    if request.method == "POST" and request.user.is_authenticated:
        if registered:
            messages.warning(request, "Вы уже записаны на это событие.")
            form = RegistrationCommentForm()
        else:
            form = RegistrationCommentForm(request.POST)
            if form.is_valid():
                if event.organizer_id == request.user.id:
                    messages.error(request, "Нельзя записаться на своё событие.")
                elif event.capacity is not None and Registration.objects.filter(event=event).count() >= event.capacity:
                    messages.error(request, "Свободных мест больше нет.")
                else:
                    try:
                        Registration.objects.create(
                            event=event,
                            user=request.user,
                            comment=form.cleaned_data.get("comment", ""),
                        )
                        messages.success(request, "Вы успешно записались на событие.")
                        return redirect("event_detail", pk=event.pk)
                    except IntegrityError:
                        messages.error(request, "Не удалось записаться (возможно, вы уже в списке).")
    else:
        form = RegistrationCommentForm()

    return render(
        request,
        "events/event_detail.html",
        {"event": event, "form": form, "registered": registered},
    )


@login_required
def event_leave(request, pk):
    if request.method != "POST":
        return redirect("event_detail", pk=pk)
    event = get_object_or_404(Event, pk=pk)
    Registration.objects.filter(event=event, user=request.user).delete()
    messages.success(request, "Запись отменена.")
    return redirect("event_detail", pk=pk)


@login_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.organizer = request.user
            ev.save()
            messages.success(request, "Событие создано.")
            return redirect("event_detail", pk=ev.pk)
    else:
        form = EventForm()
    return render(request, "events/event_form.html", {"form": form, "title_page": "Создать событие"})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk, organizer=request.user)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены.")
            return redirect("event_detail", pk=event.pk)
    else:
        form = EventForm(instance=event)
    return render(
        request,
        "events/event_form.html",
        {"form": form, "title_page": "Редактировать событие", "event": event},
    )


@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, organizer=request.user)
    if request.method != "POST":
        return redirect("event_edit", pk=pk)
    event.delete()
    return redirect("event_list")


@login_required
def profile(request):
    organized = (
        Event.objects.filter(organizer=request.user)
        .annotate(registrations_count=Count("registrations"))
        .select_related("organizer")
        .order_by("starts_at", "id")
    )
    attending = (
        Registration.objects.filter(user=request.user)
        .select_related("event")
        .order_by("-event__starts_at", "-id")
    )
    return render(
        request,
        "events/profile.html",
        {"organized_events": organized, "attending_registrations": attending},
    )
