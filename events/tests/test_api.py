from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Invitation

from .base import event, user


class EventInvitationsAPITests(TestCase):
    def setUp(self):
        self.organizer = user("org", "org@test.com")
        self.other = user("other", "other@test.com")
        self.ev = event(self.organizer, title="API Event")
        self.url = f"/api/events/{self.ev.pk}/invitations/"

    def test_get_requires_auth(self):
        client = APIClient()
        r = client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_forbidden_for_non_organizer(self):
        client = APIClient()
        client.force_authenticate(self.other)
        r = client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_returns_list_for_organizer(self):
        Invitation.objects.create(
            event=self.ev,
            email="a@test.com",
            token=Invitation.generate_token(),
            status=Invitation.Status.PENDING,
        )
        client = APIClient()
        client.force_authenticate(self.organizer)
        r = client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertIn("accept_url", r.data[0])

    def test_post_creates_invitation(self):
        client = APIClient()
        client.force_authenticate(self.organizer)
        r = client.post(self.url, {"email": "newguest@test.com"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["email"], "newguest@test.com")
        self.assertTrue(Invitation.objects.filter(event=self.ev, email="newguest@test.com").exists())

    def test_post_rejects_organizer_email(self):
        client = APIClient()
        client.force_authenticate(self.organizer)
        r = client.post(self.url, {"email": "org@test.com"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class InvitationRevokeAPITests(TestCase):
    def setUp(self):
        self.organizer = user("org2", "org2@test.com")
        self.other = user("other2", "other2@test.com")
        self.ev = event(self.organizer)
        self.inv = Invitation.objects.create(
            event=self.ev,
            email="g@test.com",
            token=Invitation.generate_token(),
            status=Invitation.Status.PENDING,
        )

    def test_delete_revokes(self):
        client = APIClient()
        client.force_authenticate(self.organizer)
        url = f"/api/invitations/{self.inv.pk}/"
        r = client.delete(url)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.REVOKED)

    def test_delete_forbidden_for_other_user(self):
        client = APIClient()
        client.force_authenticate(self.other)
        r = client.delete(f"/api/invitations/{self.inv.pk}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
