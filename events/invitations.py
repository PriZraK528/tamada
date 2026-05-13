from django.core.exceptions import ValidationError

from .models import Invitation


def create_or_refresh_invitation(event, email: str) -> Invitation:
    """Создать приглашение или обновить токен для ожидающего/отозванного."""
    email = email.strip().lower()
    org_email = (event.organizer.email or "").strip().lower()
    if org_email and email == org_email:
        raise ValidationError("Нельзя отправить приглашение на свой же email организатора.")

    accepted = Invitation.objects.filter(
        event=event,
        email=email,
        status=Invitation.Status.ACCEPTED,
    ).exists()
    if accepted:
        raise ValidationError("Этот адрес уже принял приглашение на это событие.")

    existing = Invitation.objects.filter(event=event, email=email).first()
    token = Invitation.generate_token()
    if existing:
        existing.token = token
        existing.status = Invitation.Status.PENDING
        existing.save()
        return existing
    return Invitation.objects.create(
        event=event,
        email=email,
        token=token,
        status=Invitation.Status.PENDING,
    )
