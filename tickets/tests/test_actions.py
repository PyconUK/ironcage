from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase

from . import factories
from ironcage.tests import utils

from tickets import actions
from tickets.models import TicketInvitation, Ticket
from payments import actions as payment_actions
from payments.models import Payment


class CreatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_order_for_self_individual(self):
        order = actions.create_pending_order(
            self.alice,
            Ticket.INDIVIDUAL,
            days_for_self=['sat', 'sun', 'mon']
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, Ticket.INDIVIDUAL)

    def test_order_for_self_corporate(self):
        order = actions.create_pending_order(
            self.alice,
            Ticket.CORPORATE,
            days_for_self=['sat', 'sun', 'mon'],
            company_details={
                'name': 'Sirius Cybernetics Corp.',
                'addr': 'Eadrax, Sirius Tau',
            },
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, Ticket.CORPORATE)
        self.assertEqual(order.company_name, 'Sirius Cybernetics Corp.')
        self.assertEqual(order.company_addr, 'Eadrax, Sirius Tau')

    def test_order_for_others(self):
        order = actions.create_pending_order(
            self.alice,
            Ticket.INDIVIDUAL,
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, Ticket.INDIVIDUAL)

    def test_order_for_self_and_others(self):
        order = actions.create_pending_order(
            self.alice,
            Ticket.INDIVIDUAL,
            days_for_self=['sat', 'sun', 'mon'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        self.assertEqual(self.alice.orders.count(), 1)
        self.assertIsNone(self.alice.get_ticket())

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, Ticket.INDIVIDUAL)


class UpdatePendingOrderTests(TestCase):
    def test_order_for_self_to_order_for_self(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['sat'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [{'name': 'Alice', 'days': 'Saturday', 'cost_incl_vat': 54, 'cost_excl_vat': 45}]
        )

    def test_order_for_self_to_order_for_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'bob@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
                {'name': 'carol@example.com', 'days': 'Sunday, Monday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
            ]
        )

    def test_order_for_self_to_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['sat', 'sun', 'mon'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
                {'name': 'bob@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
                {'name': 'carol@example.com', 'days': 'Sunday, Monday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
            ]
        )

    def test_individual_order_to_corporate_order(self):
        order = factories.create_pending_order_for_self()
        actions.update_pending_order(
            order,
            'corporate',
            days_for_self=['sat', 'sun', 'mon'],
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
                {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 252, 'cost_excl_vat': 210},
            ]
        )

    def test_corporate_order_to_individual_order(self):
        order = factories.create_pending_order_for_self(rate='corporate')
        actions.update_pending_order(
            order,
            'individual',
            days_for_self=['sat', 'sun', 'mon'],
        )

        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.rate, 'individual')
        self.assertEqual(order.company_name, None)
        self.assertEqual(order.company_addr, None)
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
            ]
        )


class ConfirmOrderTests(TestCase):
    def test_order_for_self(self):
        order = factories.create_pending_order_for_self()

        with utils.patched_charge_creation_success(order.total_pence_inc_vat):
            payment = payment_actions.pay_invoice_by_stripe(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(payment.charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.SUCCESSFUL)

        self.assertEqual(order.purchaser.invoices.all()[0].payments.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])

        self.assertEqual(len(mail.outbox), 1)

    def test_order_for_others(self):
        order = factories.create_pending_order_for_others()

        with utils.patched_charge_creation_success(order.total_pence_inc_vat):
            payment = payment_actions.pay_invoice_by_stripe(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(payment.charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.SUCCESSFUL)

        self.assertEqual(order.purchaser.invoices.all()[0].payments.count(), 1)
        self.assertIsNone(order.purchaser.get_ticket())

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Sunday', 'Monday'])

        self.assertEqual(len(mail.outbox), 3)

    def test_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()

        with utils.patched_charge_creation_success(order.total_pence_inc_vat):
            payment = payment_actions.pay_invoice_by_stripe(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(payment.charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.SUCCESSFUL)

        self.assertEqual(order.purchaser.invoices.all()[0].payments.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])

        ticket = TicketInvitation.objects.get(email_addr='bob@example.com').ticket
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday'])

        ticket = TicketInvitation.objects.get(email_addr='carol@example.com').ticket
        self.assertEqual(ticket.days(), ['Sunday', 'Monday'])

        self.assertEqual(len(mail.outbox), 3)

    def test_after_order_marked_as_failed(self):
        order = factories.create_pending_order_for_self()
        payment_actions.mark_payment_as_failed(order, 'There was a problem', 'ch_abcdefghijklmnopqurstuvw')

        with utils.patched_charge_creation_success(order.total_pence_inc_vat):
            payment = payment_actions.pay_invoice_by_stripe(order, 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(payment.charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.SUCCESSFUL)

        self.assertEqual(order.purchaser.invoices.all()[0].payments.count(), 1)
        self.assertIsNotNone(order.purchaser.get_ticket())

        ticket = order.purchaser.get_ticket()
        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])

    def test_sends_slack_message(self):
        backend = get_slack_backend()
        order = factories.create_pending_order_for_self()
        backend.reset_messages()

        with utils.patched_charge_creation_success(order.total_pence_inc_vat):
            payment_actions.pay_invoice_by_stripe(order, 'ch_abcdefghijklmnopqurstuvw')

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('Alice has just placed an order for 1 ticket at the individual rate', text)


class MarkOrderAsFailed(TestCase):
    def test_mark_order_as_failed(self):
        order = factories.create_pending_order_for_self()

        payment_actions.mark_payment_as_failed(order, 'There was a problem', 'ch_abcdefghijklmnopqurstuvw')

        self.assertEqual(order.payments.first().charge_failure_reason, 'There was a problem')
        self.assertEqual(order.payments.first().status, Payment.FAILED)


class MarkOrderAsErroredAfterCharge(TestCase):
    def test_mark_order_as_errored_after_charge(self):
        order = factories.create_pending_order_for_self()

        payment_actions.mark_payment_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw', order.total_pence_inc_vat)

        self.assertEqual(order.payments.first().charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.payments.first().status, Payment.ERRORED)


class CreateFreeTicketTests(TestCase):
    def test_create_free_ticket(self):
        ticket = actions.create_free_ticket('alice@example.com', 'Financial assistance')

        self.assertEqual(ticket.days(), [])
        self.assertEqual(ticket.pot, 'Financial assistance')
        self.assertEqual(ticket.invitation.email_addr, 'alice@example.com')
        self.assertEqual(len(mail.outbox), 1)


class UpdateFreeTicketTests(TestCase):
    def test_update_free_ticket(self):
        ticket = factories.create_free_ticket()

        actions.update_free_ticket(ticket, ['sat', 'sun', 'mon'])
        ticket.refresh_from_db()

        self.assertEqual(ticket.days(), ['Saturday', 'Sunday', 'Monday'])


class TicketInvitationTests(TestCase):
    def test_claim_ticket_invitation(self):
        factories.create_confirmed_order_for_others()
        bob = factories.create_user('Bob')

        invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        actions.claim_ticket_invitation(bob, invitation)

        self.assertIsNotNone(bob.get_ticket())


class ReassignTicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_reassign_assigned_ticket_with_existing_invitation(self):
        ticket = factories.create_ticket_with_claimed_invitation(self.alice)
        mail.outbox = []

        actions.reassign_ticket(ticket, 'zoe@example.com')
        self.alice.refresh_from_db()
        self.assertIsNone(self.alice.get_ticket())

        ticket.refresh_from_db()
        self.assertEqual(ticket.invitation.status, TicketInvitation.UNCLAIMED)

        self.assertEqual(len(mail.outbox), 1)

    def test_reassign_assigned_ticket_with_no_existing_invitation(self):
        ticket = factories.create_ticket(self.alice)
        mail.outbox = []

        actions.reassign_ticket(ticket, 'zoe@example.com')

        # For some reason, refresh_from_db doesn't work here (although it does
        # in test_reassign_assigned_ticket_with_existing_invitation), so let's
        # get the object from the database directly.
        # self.alice.refresh_from_db()
        alice = type(self.alice).objects.get(id=self.alice.id)
        self.assertIsNone(alice.get_ticket())

        ticket.refresh_from_db()
        self.assertEqual(ticket.invitation.status, TicketInvitation.UNCLAIMED)

        self.assertEqual(len(mail.outbox), 1)

    def test_reassign_unassigned_ticket(self):
        ticket = factories.create_ticket_with_unclaimed_invitation()
        mail.outbox = []

        actions.reassign_ticket(ticket, 'zoe@example.com')

        ticket.refresh_from_db()
        self.assertEqual(ticket.invitation.status, TicketInvitation.UNCLAIMED)

        self.assertEqual(len(mail.outbox), 1)


class OrderRefundTests(TestCase):
    def test_refund_order(self):
        order = factories.create_confirmed_order_for_self()
        mail.outbox = []

        with utils.patched_refund_creation_expected():
            actions.refund_order(order)

        self.assertEqual(order.status, 'refunded')
        self.assertEqual(order.tickets.count(), 0)

        self.assertEqual(len(mail.outbox), 1)
