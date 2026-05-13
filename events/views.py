from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode

from .forms import EventForm, InvitationEmailForm, RegistrationCommentForm
from .invitations import create_or_refresh_invitation
from .models import Event, Invitation, Registration
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
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("event_list")
    next_value = (request.POST.get("next") if submitted else None) or request.GET.get("next", "")
    return render(
        request,
        "registration/signup.html",
        {"serializer": serializer, "submitted": submitted, "next": next_value},
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
        my_reg_event_ids = Registration.objects.filter(user=request.user).values_list("event_id", flat=True)
        event = get_object_or_404(
            base_qs.filter(
                Q(is_public=True) | Q(organizer=request.user) | Q(pk__in=my_reg_event_ids)
            ),
            pk=pk,
        )
    else:
        event = get_object_or_404(base_qs.filter(is_public=True), pk=pk)

    registered = False
    if request.user.is_authenticated:
        registered = Registration.objects.filter(event=event, user=request.user).exists()

    invite_form = InvitationEmailForm()
    invitations = None
    if request.user.is_authenticated and request.user.id == event.organizer_id:
        invitations = Invitation.objects.filter(event=event).order_by("-created_at")

    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("send_invite"):
            if event.organizer_id != request.user.id:
                messages.error(request, "Только организатор может отправлять приглашения.")
            else:
                invite_form = InvitationEmailForm(request.POST)
                if invite_form.is_valid():
                    try:
                        create_or_refresh_invitation(event, invite_form.cleaned_data["email"])
                        messages.success(
                            request,
                            "Приглашение создано. Скопируйте ссылку из списка ниже и отправьте гостю.",
                        )
                    except DjangoValidationError as exc:
                        messages.error(request, " ".join(exc.messages))
                else:
                    for errs in invite_form.errors.values():
                        for err in errs:
                            messages.error(request, err)
            return redirect("event_detail", pk=event.pk)

        if request.POST.get("revoke_invitation"):
            if event.organizer_id != request.user.id:
                messages.error(request, "Только организатор может отзывать приглашения.")
            else:
                raw_id = request.POST.get("invitation_id")
                try:
                    inv_pk = int(raw_id)
                except (TypeError, ValueError):
                    messages.error(request, "Некорректный идентификатор приглашения.")
                else:
                    inv = Invitation.objects.filter(pk=inv_pk, event=event).first()
                    if not inv:
                        messages.error(request, "Приглашение не найдено.")
                    elif inv.status != Invitation.Status.PENDING:
                        messages.warning(
                            request,
                            "Отозвать можно только приглашение в статусе «ожидает ответа».",
                        )
                    else:
                        inv.status = Invitation.Status.REVOKED
                        inv.save(update_fields=["status"])
                        messages.success(request, "Приглашение отозвано.")
            return redirect("event_detail", pk=event.pk)

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
        {
            "event": event,
            "form": form,
            "registered": registered,
            "invite_form": invite_form,
            "invitations": invitations,
        },
    )


def invitation_accept(request, token):
    invitation = get_object_or_404(
        Invitation.objects.select_related("event", "event__organizer"),
        token=token,
    )
    event = invitation.event

    if invitation.status != Invitation.Status.PENDING:
        return render(
            request,
            "events/invitation_status.html",
            {"invitation": invitation, "event": event},
            status=410,
        )

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(request, "Войдите в аккаунт, чтобы принять приглашение.")
            next_path = reverse("invitation_accept", kwargs={"token": token})
            return redirect(f"{reverse('login')}?{urlencode({'next': next_path})}")
        user_email = (request.user.email or "").strip().lower()
        if not user_email:
            messages.error(
                request,
                "В профиле не указан email. Укажите в настройках аккаунта тот же адрес, что в приглашении.",
            )
            return redirect("invitation_accept", token=token)
        if user_email != invitation.email:
            messages.error(
                request,
                "Email в вашем профиле не совпадает с адресом в приглашении. Войдите под нужным пользователем или обновите email.",
            )
            return redirect("invitation_accept", token=token)
        if event.organizer_id == request.user.id:
            messages.error(request, "Организатор не может принять приглашение на своё событие.")
            return redirect("invitation_accept", token=token)

        if Registration.objects.filter(event=event, user=request.user).exists():
            invitation.status = Invitation.Status.ACCEPTED
            invitation.save(update_fields=["status"])
            messages.info(request, "Вы уже в списке участников.")
            return redirect("event_detail", pk=event.pk)

        if event.capacity is not None and Registration.objects.filter(event=event).count() >= event.capacity:
            messages.error(request, "Свободных мест на это событие больше нет.")
            return redirect("invitation_accept", token=token)

        try:
            with transaction.atomic():
                Registration.objects.create(event=event, user=request.user, comment="")
                invitation.status = Invitation.Status.ACCEPTED
                invitation.save(update_fields=["status"])
        except IntegrityError:
            messages.error(request, "Не удалось завершить запись. Попробуйте ещё раз.")
            return redirect("invitation_accept", token=token)

        messages.success(request, "Вы записаны на событие по приглашению.")
        return redirect("event_detail", pk=event.pk)

    login_next = reverse("invitation_accept", kwargs={"token": token})
    return render(
        request,
        "events/invitation_accept.html",
        {
            "invitation": invitation,
            "event": event,
            "login_next": login_next,
        },
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
