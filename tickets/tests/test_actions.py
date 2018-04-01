from unittest.mock import patch, MagicMock

from django.test import TestCase

from payments.models import Invoice
from tickets import actions
from tickets.models import Ticket
from tickets.tests import factories


class CreateTicketTests(TestCase):

    def setUp(self):
        self.user = factories.create_user()

    @patch('tickets.models.Ticket.objects.create_for_user')
    def test_create_individual_ticket(self, create_for_user):
        # arrange

        # act
        actions.create_ticket(self.user, Ticket.INDIVIDUAL, days=['sat', 'sun', 'mon'])

        # assert
        create_for_user.assert_called_once_with(
            self.user, Ticket.INDIVIDUAL, ['sat', 'sun', 'mon']
        )


class CreateTicketWithInvitationTests(TestCase):

    def setUp(self):
        self.user = factories.create_user()

    @patch('tickets.models.Ticket.objects.create_with_invitation')
    def test_create_ticket_with_invitation(self, create_with_invitation):
        # arrange

        # act
        actions.create_ticket_with_invitation(self.user, Ticket.CORPORATE, days=['sat', 'sun', 'mon'])

        # assert
        create_with_invitation.assert_called_once_with(
            self.user, Ticket.CORPORATE, ['sat', 'sun', 'mon']
        )


class CreateInvoiceWithTicketsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def setUp(self):
        self.invoice_mock = MagicMock()
        self.create_invoice_patch = patch('payments.actions.create_new_invoice',
                                          return_value=self.invoice_mock)
        self.create_invoice = self.create_invoice_patch.start()

    def tearDown(self):
        self.create_invoice_patch.stop()

    @patch('tickets.actions.create_ticket')
    @patch('tickets.actions.create_ticket_with_invitation')
    @patch.object(Invoice, 'add_item')
    def test_order_for_self_individual(self, add_item, create_ticket_with_invite,
                                       create_ticket):
        # arrange

        # act
        actions.create_invoice_with_tickets(
            self.alice,
            Ticket.INDIVIDUAL,
            days_for_self=['sat', 'sun', 'mon']
        )

        # assert
        self.create_invoice.assert_called_once_with(self.alice, None, None)
        create_ticket.assert_called_once_with(self.alice, Ticket.INDIVIDUAL, ['sat', 'sun', 'mon'])
        self.invoice_mock.add_item.assert_called_once()
        create_ticket_with_invite.assert_not_called()

    @patch('tickets.actions.create_ticket')
    @patch('tickets.actions.create_ticket_with_invitation')
    def test_order_for_self_corporate(self, create_ticket_with_invite,
                                      create_ticket):
        # arrange

        # act
        actions.create_invoice_with_tickets(
            self.alice,
            Ticket.CORPORATE,
            days_for_self=['sat', 'sun', 'mon'],
            company_details={
                'name': 'Sirius Cybernetics Corp.',
                'addr': 'Eadrax, Sirius Tau',
            },
        )

        # assert
        self.create_invoice.assert_called_once_with(self.alice, 'Sirius Cybernetics Corp.', 'Eadrax, Sirius Tau')
        create_ticket.assert_called_once_with(self.alice, Ticket.CORPORATE, ['sat', 'sun', 'mon'])
        self.invoice_mock.add_item.assert_called_once()
        create_ticket_with_invite.assert_not_called()

    @patch('tickets.actions.create_ticket')
    @patch('tickets.actions.create_ticket_with_invitation')
    def test_order_for_others(self, create_ticket_with_invite,
                              create_ticket):
        # arrange

        # act
        actions.create_invoice_with_tickets(
            self.alice,
            Ticket.INDIVIDUAL,
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        # assert
        self.create_invoice.assert_called_once_with(self.alice, None, None)
        self.assertEqual(create_ticket_with_invite.call_count, 2)
        create_ticket_with_invite.assert_any_call('bob@example.com', Ticket.INDIVIDUAL, ['sat', 'sun'])
        create_ticket_with_invite.assert_any_call('carol@example.com', Ticket.INDIVIDUAL, ['sun', 'mon'])
        self.assertEqual(self.invoice_mock.add_item.call_count, 2)
        create_ticket.assert_not_called()

    @patch('tickets.actions.create_ticket')
    @patch('tickets.actions.create_ticket_with_invitation')
    def test_order_for_self_and_others(self, create_ticket_with_invite,
                                       create_ticket):
        # arrange

        # act
        actions.create_invoice_with_tickets(
            self.alice,
            Ticket.INDIVIDUAL,
            days_for_self=['sat', 'sun', 'mon'],
            email_addrs_and_days_for_others=[
                ('bob@example.com', ['sat', 'sun']),
                ('carol@example.com', ['sun', 'mon']),
            ]
        )

        # assert
        self.create_invoice.assert_called_once_with(self.alice, None, None)
        create_ticket.assert_called_once_with(self.alice, Ticket.INDIVIDUAL, ['sat', 'sun', 'mon'])
        self.assertEqual(create_ticket_with_invite.call_count, 2)
        create_ticket_with_invite.assert_any_call('bob@example.com', Ticket.INDIVIDUAL, ['sat', 'sun'])
        create_ticket_with_invite.assert_any_call('carol@example.com', Ticket.INDIVIDUAL, ['sun', 'mon'])
        self.assertEqual(self.invoice_mock.add_item.call_count, 3)


class UpdateUnpaidOrderTests(TestCase):
    pass


class CreateFreeTicketTests(TestCase):
    pass


