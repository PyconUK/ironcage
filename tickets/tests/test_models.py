from django.test import TestCase
from django.core.exceptions import ValidationError
from . import factories

from tickets.models import Ticket, TicketInvitation


class CreateTicketForUserTests(TestCase):

    @classmethod
    def setUp(cls):
        cls.alice = factories.create_user()

    def test_create_ticket_for_user_requires_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_for_user(
                self.alice,
                Ticket.INDIVIDUAL,
                days=[]
            )

        # assert
        with self.assertRaises(Ticket.DoesNotExist):
            # act
            self.assertIsNone(self.alice.ticket)

    def test_create_ticket_for_user_requires_valid_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_for_user(
                self.alice,
                Ticket.INDIVIDUAL,
                days=['apr', 'may', 'jun']
            )

        # assert
        with self.assertRaises(Ticket.DoesNotExist):
            # act
            self.assertIsNone(self.alice.ticket)

    def test_create_ticket_for_user_requires_all_valid_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_for_user(
                self.alice,
                Ticket.INDIVIDUAL,
                days=['sat', 'sun', 'jun']
            )

        # assert
        with self.assertRaises(Ticket.DoesNotExist):
            # act
            self.assertIsNone(self.alice.ticket)

    def test_create_ticket_for_user(self):

        ticket = Ticket.objects.create_for_user(
            self.alice,
            Ticket.INDIVIDUAL,
            days=['sat', 'sun', 'mon']
        )

        self.assertTrue(isinstance(self.alice.ticket, Ticket))
        self.assertIsNotNone(self.alice.ticket.created_at)
        self.assertEqual(ticket.owner, self.alice)
        self.assertEqual(ticket.rate, Ticket.INDIVIDUAL)

        self.assertTrue(ticket.sat)
        self.assertTrue(ticket.sun)
        self.assertTrue(ticket.mon)
        self.assertFalse(ticket.tue)
        self.assertFalse(ticket.wed)

    def test_create_non_free_ticket_for_user_invalid_with_no_invoice_or_payment(self):

        ticket = Ticket.objects.create_for_user(
            self.alice,
            Ticket.INDIVIDUAL,
            days=['sat', 'sun', 'mon']
        )

        self.assertFalse(ticket.valid)

    def test_create_free_ticket_for_user_valid_with_no_invoice_or_payment(self):

        ticket = Ticket.objects.create_for_user(
            self.alice,
            Ticket.FREE,
            days=['sat', 'sun', 'mon']
        )

        self.assertTrue(ticket.valid)


class CreateTicketWithInvitationTests(TestCase):

    def test_create_ticket_with_invitation_requires_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_with_invitation(
                'alice@example.com',
                Ticket.CORPORATE,
                days=[]
            )

    def test_create_ticket_with_invitation_requires_valid_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_with_invitation(
                'alice@example.com',
                Ticket.CORPORATE,
                days=['apr', 'may', 'jun']
            )

    def test_create_ticket_with_invitation_requires_all_valid_days(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            Ticket.objects.create_with_invitation(
                'alice@example.com',
                Ticket.CORPORATE,
                days=['sat', 'sun', 'jun']
            )

    def test_create_ticket_with_invitation(self):

        ticket = Ticket.objects.create_with_invitation(
            'alice@example.com',
            Ticket.CORPORATE,
            days=['mon', 'tue', 'wed']
        )

        self.assertEqual(ticket.rate, Ticket.CORPORATE)

        self.assertIsNotNone(ticket.invitation)
        self.assertEqual(ticket.invitation.email_addr, 'alice@example.com')
        self.assertEqual(ticket.invitation.status, TicketInvitation.UNCLAIMED)

        self.assertFalse(ticket.sat)
        self.assertFalse(ticket.sun)
        self.assertTrue(ticket.mon)
        self.assertTrue(ticket.tue)
        self.assertTrue(ticket.wed)


class CreateFreeTicketWithInvitationTests(TestCase):

    def test_create_free_ticket_with_invitation(self):

        ticket = Ticket.objects.create_free_with_invitation(
            'alice@example.com',
            'ming vase'
        )

        self.assertEqual(ticket.rate, Ticket.FREE)
        self.assertEqual(ticket.pot, 'ming vase')

        self.assertIsNotNone(ticket.invitation)
        self.assertEqual(ticket.invitation.email_addr, 'alice@example.com')
        self.assertEqual(ticket.invitation.status, TicketInvitation.UNCLAIMED)

        self.assertFalse(ticket.sat)
        self.assertFalse(ticket.sun)
        self.assertFalse(ticket.mon)
        self.assertFalse(ticket.tue)
        self.assertFalse(ticket.wed)


class TicketTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.self_ticket = factories.create_ticket_for_self()
        cls.unclaimed_ticket = factories.create_ticket_with_unclaimed_invitation_ticket()

    def test_cost_incl_vat_for_ticket_with_owner(self):
        self.assertEqual(self.self_ticket.cost_incl_vat(), 126)  # 126 == (3 * 30 + 15) * 1.2

    def test_cost_incl_vat_for_ticket_with_no_owner(self):
        self.assertEqual(self.unclaimed_ticket.cost_incl_vat(), 126)  # 126 == (3 * 30 + 15) * 1.2

    def test_cost_excl_vat_for_ticket_with_owner(self):
        self.assertEqual(self.self_ticket.cost_excl_vat(), 105)  # 105 == 3 * 30 + 15

    def test_cost_excl_vat_for_ticket_with_no_owner(self):
        self.assertEqual(self.unclaimed_ticket.cost_excl_vat(), 105)  # 105 == 3 * 30 + 15
