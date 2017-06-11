import re

from django.core import mail
from django.test import TestCase

from . import factories

from tickets.mailer import send_invitation_mail
from tickets.models import TicketInvitation


class MailerTests(TestCase):
    def test_send_invitation_mail(self):
        factories.create_confirmed_order_for_others()

        mail.outbox = []

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        send_invitation_mail(invitation)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2017 <tickets@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2017 ticket invitation ({invitation.ticket.ticket_id})')
        self.assertTrue(re.search(r'Alice has purchased you a ticket for PyCon UK 2017', email.body))
        self.assertTrue(re.search(r'http://localhost:8000/tickets/invitations/\w{12}/', email.body))
