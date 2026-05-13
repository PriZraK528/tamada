from django.test import TestCase

from events.models import Invitation

from .base import event, user


class InvitationModelTests(TestCase):
    def test_save_normalizes_email(self):
        org = user()
        ev = event(org)
        inv = Invitation(event=ev, email="  Mixed@Case.COM ", token=Invitation.generate_token())
        inv.save()
        self.assertEqual(inv.email, "mixed@case.com")

    def test_save_generates_token_if_missing(self):
        org = user()
        ev = event(org)
        inv = Invitation(event=ev, email="x@y.com", status=Invitation.Status.PENDING)
        inv.save()
        self.assertTrue(inv.token)
