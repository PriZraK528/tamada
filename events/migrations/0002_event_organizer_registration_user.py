# Data migration: organizer + user; drop legacy name/email.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forwards_assign_organizer_and_user(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    Event = apps.get_model("events", "Event")
    Registration = apps.get_model("events", "Registration")

    first = User.objects.order_by("pk").first()
    if not first:
        Registration.objects.all().delete()
        Event.objects.all().delete()
        return

    Event.objects.filter(organizer__isnull=True).update(organizer_id=first.pk)

    for reg in Registration.objects.all():
        u = User.objects.filter(email__iexact=reg.email).first()
        if u:
            Registration.objects.filter(pk=reg.pk).update(user_id=u.pk)
        else:
            reg.delete()

    Registration.objects.filter(user_id__isnull=True).delete()

    # remove duplicate (event, user), keep smallest id
    seen = set()
    for reg in Registration.objects.order_by("pk"):
        key = (reg.event_id, reg.user_id)
        if key in seen:
            reg.delete()
        else:
            seen.add(key)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="organizer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organized_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="registration",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="event_registrations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(forwards_assign_organizer_and_user, noop_reverse),
        migrations.RemoveConstraint(
            model_name="registration",
            name="uniq_registration_event_email",
        ),
        migrations.AddConstraint(
            model_name="registration",
            constraint=models.UniqueConstraint(
                fields=("event", "user"),
                name="uniq_registration_event_user",
            ),
        ),
        migrations.RemoveField(model_name="registration", name="name"),
        migrations.RemoveField(model_name="registration", name="email"),
        migrations.AlterField(
            model_name="event",
            name="organizer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organized_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="event_registrations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
