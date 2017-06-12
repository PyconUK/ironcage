from django.core import mail
from django.test import TestCase

from . import factories
from . import utils

from tickets import actions
from tickets.models import TicketInvitation


class CreatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

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


class UpdatePendingOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'corporate',
            days_for_self=['fri', 'sat', 'sun']
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'corporate')
        self.assertEqual(
            order.ticket_details(),
            [{'name': 'Alice', 'days': 'Friday, Saturday, Sunday', 'cost_incl_vat': 180, 'cost_excl_vat': 150}]
        )

    def test_order_for_self_to_order_for_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'corporate',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'corporate')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'bob@example.com', 'days': 'Friday, Saturday', 'cost_incl_vat': 132, 'cost_excl_vat': 110},
                {'name': 'carol@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 132, 'cost_excl_vat': 110},
            ]
        )

    def test_order_for_self_to_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'corporate',
            days_for_self=['fri', 'sat', 'sun'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'corporate')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Friday, Saturday, Sunday', 'cost_incl_vat': 180, 'cost_excl_vat': 150},
                {'name': 'bob@example.com', 'days': 'Friday, Saturday', 'cost_incl_vat': 132, 'cost_excl_vat': 110},
                {'name': 'carol@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 132, 'cost_excl_vat': 110},
            ]
        )


class ConfirmOrderTests(TestCase):
    def test_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertEqual(order.purchaser.tickets.count(), 1)

        ticket = order.purchaser.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        self.assertEqual(len(mail.outbox), 1)

    def test_order_for_others(self):
        order = factories.create_pending_order_for_others()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertEqual(order.purchaser.tickets.count(), 0)

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        self.assertEqual(len(mail.outbox), 3)

    def test_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertEqual(order.purchaser.tickets.count(), 1)

        ticket = order.purchaser.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Friday', 'Saturday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        self.assertEqual(len(mail.outbox), 3)

    def test_after_order_marked_as_failed(self):
        order = factories.create_pending_order_for_self()
        actions.mark_order_as_failed(order, 'There was a problem')

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(order.purchaser.orders.count(), 1)
        self.assertEqual(order.purchaser.tickets.count(), 1)

        ticket = order.purchaser.ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])


class MarkOrderAsFailed(TestCase):
    def test_mark_order_as_failed(self):
        order = factories.create_pending_order_for_self()

        actions.mark_order_as_failed(order, 'There was a problem')

        self.assertEqual(order.stripe_charge_failure_reason, 'There was a problem')
        self.assertEqual(order.status, 'failed')


class ProcessStripeChargeTests(TestCase):
    def setUp(self):
        self.order = factories.create_pending_order_for_self()

    def test_process_stripe_charge_success(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_success():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'successful')

    def test_process_stripe_charge_failure(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_failure():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        factories.create_confirmed_order_for_others()
        bob = factories.create_user('Bob')

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.tickets.get())
