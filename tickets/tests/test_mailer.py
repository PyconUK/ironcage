import re

from django.core import mail
from django.test import TestCase

from . import factories

from tickets.mailer import send_invitation_mail, send_order_confirmation_mail
from tickets.models import TicketInvitation


class MailerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(email_addr='alice@example.com')

    def test_send_invitation_mail(self):
        factories.create_confirmed_order_for_others(self.alice)
        mail.outbox = []

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        send_invitation_mail(invitation.ticket)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bob@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 ticket invitation ({invitation.ticket.ticket_id})')
        self.assertTrue(re.search(r'Alice has purchased you a ticket for PyCon UK 2018', email.body))
        self.assertTrue(re.search(r'http://testserver/tickets/invitations/\w{12}/', email.body))

    def test_send_invitation_mail_for_free_ticket(self):
        factories.create_free_ticket(self.alice)
        mail.outbox = []

        invitation = TicketInvitation.objects.get(email_addr='alice@example.com')
        send_invitation_mail(invitation.ticket)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 ticket invitation ({invitation.ticket.ticket_id})')
        self.assertTrue(re.search(r'You have been assigned a ticket for PyCon UK 2018', email.body))
        self.assertTrue(re.search(r'http://testserver/tickets/invitations/\w{12}/', email.body))

    def test_send_order_confirmation_mail_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 1 ticket for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/tickets/orders/{order.order_id}/receipt/', email.body))
        self.assertFalse(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('We look forward to seeing you in Cardiff', email.body))

    def test_send_order_confirmation_mail_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 2 tickets for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/tickets/orders/{order.order_id}/receipt/', email.body))
        self.assertTrue(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('bob@example.com', email.body))
        self.assertTrue(re.search('carol@example.com', email.body))
        self.assertFalse(re.search('We look forward to seeing you in Cardiff', email.body))

    def test_send_order_confirmation_mail_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2018 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f'PyCon UK 2018 order confirmation ({order.order_id})')
        self.assertTrue(re.search(r'You have purchased 3 tickets for PyCon UK 2018', email.body))
        self.assertTrue(re.search(fr'http://testserver/tickets/orders/{order.order_id}/receipt/', email.body))
        self.assertTrue(re.search('Ticket invitations have been sent to the following', email.body))
        self.assertTrue(re.search('bob@example.com', email.body))
        self.assertTrue(re.search('carol@example.com', email.body))
        self.assertTrue(re.search('We look forward to seeing you in Cardiff', email.body))
