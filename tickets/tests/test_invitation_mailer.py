import re

from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from tickets import actions
from tickets.invitation_mailer import send_invitation_mail
from tickets.models import TicketInvitation


class InvitationMailerTests(TestCase):
    def test_send_invitation_mail(self):
        alice = User.objects.create_user(username='Alice')
        actions.place_order_for_others(
            alice,
            'individual',
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )
        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')

        send_invitation_mail(invitation)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2017 <tickets@pyconuk.org>')
        self.assertEqual(email.subject, 'PyCon UK 2017 ticket invitation (9A19)')
        self.assertTrue(re.search(r'http://localhost:8000/tickets/invitations/\w{12}/', email.body))
