from django.test import TestCase
from django.urls import reverse

from events.invitations import create_or_refresh_invitation
from events.models import Invitation, Registration

from .base import event, user


class InvitationAcceptViewTests(TestCase):
    def setUp(self):
        self.organizer = user("orgv", "orgv@test.com")
        self.guest = user("guestv", "guestv@test.com")
        self.ev = event(self.organizer, title="Приём")
        self.inv = create_or_refresh_invitation(self.ev, "guestv@test.com")

    def test_get_pending_returns_200(self):
        r = self.client.get(reverse("invitation_accept", kwargs={"token": self.inv.token}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Приглашение для")

    def test_get_non_pending_returns_410(self):
        self.inv.status = Invitation.Status.REVOKED
        self.inv.save(update_fields=["status"])
        r = self.client.get(reverse("invitation_accept", kwargs={"token": self.inv.token}))
        self.assertEqual(r.status_code, 410)

    def test_get_unknown_token_404(self):
        r = self.client.get(reverse("invitation_accept", kwargs={"token": "invalid-token-xxx"}))
        self.assertEqual(r.status_code, 404)

    def test_post_accepts_and_registers(self):
        self.client.force_login(self.guest)
        url = reverse("invitation_accept", kwargs={"token": self.inv.token})
        r = self.client.post(url, follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], reverse("event_detail", kwargs={"pk": self.ev.pk}))
        self.assertTrue(Registration.objects.filter(event=self.ev, user=self.guest).exists())
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.ACCEPTED)

    def test_post_redirects_unauthenticated_to_login_with_next(self):
        url = reverse("invitation_accept", kwargs={"token": self.inv.token})
        r = self.client.post(url, follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r["Location"])
        self.assertIn("next=", r["Location"])


class EventDetailViewTests(TestCase):
    def setUp(self):
        self.organizer = user("orgd", "orgd@test.com")
        self.attendee = user("att", "att@test.com")
        self.public_ev = event(self.organizer, title="Публичное", is_public=True)
        self.private_ev = event(self.organizer, title="Закрытое", is_public=False)

    def test_private_event_visible_to_registered_user(self):
        Registration.objects.create(event=self.private_ev, user=self.attendee, comment="")
        self.client.force_login(self.attendee)
        r = self.client.get(reverse("event_detail", kwargs={"pk": self.private_ev.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Закрытое")

    def test_private_event_hidden_from_anonymous(self):
        r = self.client.get(reverse("event_detail", kwargs={"pk": self.private_ev.pk}))
        self.assertEqual(r.status_code, 404)

    def test_organizer_revokes_pending_invitation(self):
        self.client.force_login(self.organizer)
        inv = create_or_refresh_invitation(self.public_ev, "guest@example.com")
        url = reverse("event_detail", kwargs={"pk": self.public_ev.pk})
        r = self.client.post(
            url,
            {"revoke_invitation": "1", "invitation_id": str(inv.pk)},
            follow=False,
        )
        self.assertEqual(r.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invitation.Status.REVOKED)
