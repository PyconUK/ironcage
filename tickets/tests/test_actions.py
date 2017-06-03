from django.core import mail
from django.test import TestCase

from accounts.models import User

from .utils import patched_charge_creation_failure, patched_charge_creation_success

from tickets import actions
from tickets.models import TicketInvitation


class CreatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')

    def test_order_for_self(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 0)

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')

    def test_order_for_others(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 0)

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')

    def test_order_for_self_and_others(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 0)

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')


class ConfirmOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')

    def test_order_for_self(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 1)

        ticket = self.alice.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        self.assertEqual(len(mail.outbox), 0)

    def test_order_for_others(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 0)

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        self.assertEqual(len(mail.outbox), 2)

    def test_order_for_self_and_others(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 1)

        ticket = self.alice.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        self.assertEqual(len(mail.outbox), 2)

    def test_after_order_marked_as_failed(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        actions.mark_order_as_failed(order, 'There was a problem')

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertEqual(self.alice.tickets.count(), 1)

        ticket = self.alice.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        self.assertEqual(len(mail.outbox), 0)


class MarkOrderAsFailed(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')

    def test_mark_order_as_failed(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        actions.mark_order_as_failed(order, 'There was a problem')

        self.assertEqual(order.stripe_charge_failure_reason, 'There was a problem')
        self.assertEqual(order.status, 'failed')


class ProcessStripeChargeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')
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

    def test_process_stripe_charge_failure(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with patched_charge_creation_failure():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')
        bob = User.objects.create_user(email_addr='bob@example.com', name='Bob')
        order = actions.place_order_for_others(
            alice,
            'individual',
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.tickets.get())
