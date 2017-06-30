from django_slack.utils import get_backend as get_slack_backend

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

    def test_order_for_self_individual(self):
        order = actions.create_pending_order(
            self.alice,
            'individual',
            days_for_self=['thu', 'fri', 'sat']
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')

    def test_order_for_self_corporate(self):
        order = actions.create_pending_order(
            self.alice,
            'corporate',
            days_for_self=['thu', 'fri', 'sat'],
            company_details={
                'name': 'Sirius Cybernetics Corp.',
                'addr': 'Eadrax, Sirius Tau',
            },
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'corporate')
        self.assertEqual(order.company_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.company_addr, 'Eadrax, Sirius Tau')

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
        self.assertIsNone(self.alice.get_ticket())

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
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')


class UpdatePendingOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['fri'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [{'name': 'Alice', 'days': 'Friday', 'cost_incl_vat': 54, 'cost_excl_vat': 45}]
        )

    def test_order_for_self_to_order_for_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'bob@example.com', 'days': 'Friday, Saturday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
                {'name': 'carol@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
            ]
        )

    def test_order_for_self_to_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['fri', 'sat', 'sun'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Friday, Saturday, Sunday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
                {'name': 'bob@example.com', 'days': 'Friday, Saturday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
                {'name': 'carol@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
            ]
        )

    def test_individual_order_to_corporate_order(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'corporate',
            days_for_self=['fri', 'sat', 'sun'],
            company_details={
                'name': 'Sirius Cybernetics Corp.',
                'addr': 'Eadrax, Sirius Tau',
            },
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'corporate')
        self.assertEqual(order.company_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.company_addr, 'Eadrax, Sirius Tau')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Friday, Saturday, Sunday', 'cost_incl_vat': 252, 'cost_excl_vat': 210},
            ]
        )

    def test_corporate_order_to_individual_order(self):
        order = factories.create_pending_order_for_self(rate='corporate')
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['fri', 'sat', 'sun'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(order.company_name, None)
        self.assertEqual(order.company_addr, None)
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Friday, Saturday, Sunday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
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
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
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
        self.assertIsNone(order.purchaser.get_ticket())

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
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
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
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
        self.assertEqual(ticket.days(), ['Thursday', 'Friday', 'Saturday'])

    def test_sends_slack_message(self):
        backend = get_slack_backend()
        order = factories.create_pending_order_for_self()
        backend.reset_messages()

        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('Alice has just placed an order for 1 ticket at the individual rate', text)


class MarkOrderAsFailed(TestCase):
    def test_mark_order_as_failed(self):
        order = factories.create_pending_order_for_self()

        actions.mark_order_as_failed(order, 'There was a problem')

        self.assertEqual(order.stripe_charge_failure_reason, 'There was a problem')
        self.assertEqual(order.status, 'failed')


class MarkOrderAsErroredAfterCharge(TestCase):
    def test_mark_order_as_errored_after_charge(self):
        order = factories.create_pending_order_for_self()

        actions.mark_order_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.status, 'errored')


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

    def test_process_stripe_charge_error_after_charge(self):
        factories.create_confirmed_order_for_self(self.order.purchaser)
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        with utils.patched_charge_creation_success(), utils.patched_refund_creation_expected():
            actions.process_stripe_charge(self.order, token)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'errored')
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        factories.create_confirmed_order_for_others()
        bob = factories.create_user('Bob')

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.get_ticket())
