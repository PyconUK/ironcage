from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from .utils import patched_charge_creation_failure, patched_charge_creation_success

from tickets import actions
from tickets.models import TicketInvitation


class OrderCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='Alice')

    def test_place_order_for_self(self):
        actions.place_order_for_self(
            self.alice,
            'individual',
            ['thu', 'fri', 'sat']
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 1)

        order = self.alice.orders.all()[0]
        self.assertEqual(order.rate, 'individual')

        ticket = self.alice.tickets.all()[0]
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

    def test_place_order_for_others(self):
        actions.place_order_for_others(
            self.alice,
            'individual',
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 0)

        order = self.alice.orders.all()[0]
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(order.unclaimed_tickets().count(), 2)

        ticket = order.unclaimed_tickets().get(invitations__email_addr='bob@example.com')
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])

    def test_place_order_for_self_and_others(self):
        actions.place_order_for_self_and_others(
            self.alice,
            'individual',
            ['thu', 'fri', 'sat'],
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 1)

        order = self.alice.orders.all()[0]
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(order.unclaimed_tickets().count(), 2)

        ticket = self.alice.tickets.all()[0]
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        ticket = order.unclaimed_tickets().get(invitations__email_addr='bob@example.com')
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])


class ProcessStripeChargeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(username='Alice')
        cls.order = actions.place_order_for_self_and_others(
            alice,
            'individual',
            ['thu', 'fri', 'sat'],
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

    def setUp(self):
        self.order.refresh_from_db()

    def test_process_stripe_charge_success(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with patched_charge_creation_success():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'successful')
        self.assertEqual(len(mail.outbox), 2)

    def test_process_stripe_charge_failure(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with patched_charge_creation_failure():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')
        self.assertEqual(len(mail.outbox), 0)


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        alice = User.objects.create_user(username='Alice')
        bob = User.objects.create_user(username='Bob')
        actions.place_order_for_others(
            alice,
            'individual',
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.tickets.get())
