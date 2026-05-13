from django.core.exceptions import ValidationError
from django.test import TestCase

from events.invitations import create_or_refresh_invitation
from events.models import Invitation

from .base import event, user


class CreateOrRefreshInvitationTests(TestCase):
    def setUp(self):
        self.organizer = user("org", "org@example.com")
        self.ev = event(self.organizer, title="Встреча")

    def test_creates_invitation(self):
        inv = create_or_refresh_invitation(self.ev, "  Guest@Example.com ")
        self.assertEqual(inv.email, "guest@example.com")
        self.assertEqual(inv.status, Invitation.Status.PENDING)
        self.assertTrue(inv.token)

    def test_refreshes_pending_token(self):
        inv1 = create_or_refresh_invitation(self.ev, "g@example.com")
        old_token = inv1.token
        inv2 = create_or_refresh_invitation(self.ev, "G@Example.com")
        inv1.refresh_from_db()
        self.assertEqual(inv1.pk, inv2.pk)
        self.assertNotEqual(inv1.token, old_token)
        self.assertEqual(inv1.status, Invitation.Status.PENDING)

    def test_refreshes_revoked(self):
        inv = create_or_refresh_invitation(self.ev, "g@example.com")
        inv.status = Invitation.Status.REVOKED
        inv.save(update_fields=["status"])
        refreshed = create_or_refresh_invitation(self.ev, "g@example.com")
        self.assertEqual(refreshed.pk, inv.pk)
        self.assertEqual(refreshed.status, Invitation.Status.PENDING)

    def test_rejects_organizer_email(self):
        with self.assertRaises(ValidationError):
            create_or_refresh_invitation(self.ev, "Org@Example.com")

    def test_rejects_when_already_accepted(self):
        create_or_refresh_invitation(self.ev, "g@example.com")
        Invitation.objects.filter(event=self.ev, email="g@example.com").update(
            status=Invitation.Status.ACCEPTED
        )
        with self.assertRaises(ValidationError):
            create_or_refresh_invitation(self.ev, "g@example.com")

    def test_when_organizer_has_no_email_guest_can_be_invited(self):
        org = user("noemail", email="")
        ev = event(org)
        inv = create_or_refresh_invitation(ev, "any@example.com")
        self.assertEqual(inv.email, "any@example.com")
