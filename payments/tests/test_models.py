from django.test import TestCase

from django.db.utils import IntegrityError

from payments.models import (
    InvoiceHasPaymentsException,
    STANDARD_RATE_VAT,
    ZERO_RATE_VAT,
)
from payments.tests import factories
from tickets.tests import factories as ticket_factories


class AddInvoiceRowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def test_add_invoice_row_to_invoice(self):
        invoice_row = self.invoice.add_row(self.ticket)

        self.assertEqual(self.invoice.rows.count(), 1)

        self.assertEqual(invoice_row.invoice_item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, STANDARD_RATE_VAT)

        self.assertEqual(self.invoice.total, invoice_row.total_inc_vat)

    def test_add_invoice_row_to_invoice_zero_vat(self):
        invoice_row = self.invoice.add_row(self.ticket, ZERO_RATE_VAT)

        self.assertEqual(self.invoice.rows.count(), 1)

        self.assertEqual(invoice_row.invoice_item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, ZERO_RATE_VAT)

        self.assertEqual(self.invoice.total, invoice_row.total_inc_vat)

    def test_add_same_item_multiple_times_to_invoice_fails(self):
        self.invoice.add_row(self.ticket)

        with self.assertRaises(IntegrityError):
            self.invoice.add_row(self.ticket)

    def test_add_two_items_to_invoice(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket()

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_incl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.invoice.add_row(self.ticket)
        self.invoice.add_row(ticket_2)

        # assert
        self.assertEqual(self.invoice.rows.count(), 2)
        self.assertEqual(self.invoice.total, total_ticket_cost)

    def test_add_two_items_to_invoice_different_vat_rates(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket()

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_excl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.invoice.add_row(self.ticket)
        self.invoice.add_row(ticket_2, ZERO_RATE_VAT)

        # assert
        self.assertEqual(self.invoice.rows.count(), 2)
        self.assertEqual(self.invoice.total, total_ticket_cost)

    def test_add_invoice_row_to_invoice_with_payment_fails(self):
        self.invoice.add_row(self.ticket)
        factories.make_payment(self.invoice)

        ticket_2 = ticket_factories.create_ticket()

        with self.assertRaises(InvoiceHasPaymentsException):
            self.invoice.add_row(ticket_2)


class AddCreditNoteRowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.credit_note = factories.create_credit_note(cls.alice)

    def test_add_invoice_row_to_credit_note(self):
        invoice_row = self.credit_note.add_row(self.ticket)

        self.assertEqual(self.credit_note.rows.count(), 1)

        self.assertEqual(invoice_row.invoice_item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, STANDARD_RATE_VAT)

        self.assertEqual(self.credit_note.total, -invoice_row.total_inc_vat)

    def test_add_two_items_to_credit_note(self):
        # arrange
        bob = factories.create_user()
        ticket_2 = ticket_factories.create_ticket(bob)

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_incl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.credit_note.add_row(self.ticket)
        self.credit_note.add_row(ticket_2)

        # assert
        self.assertEqual(self.credit_note.rows.count(), 2)
        self.assertEqual(self.credit_note.total, -total_ticket_cost)


class InvoiceRowIncVatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def test_inc_standard_vat(self):
        invoice_row = factories.add_invoice_row(
            item=self.ticket,
            user=self.alice,
            invoice=self.invoice
        )

        self.assertEqual(invoice_row.total_inc_vat, self.ticket.cost_incl_vat())

    def test_inc_zero_vat(self):
        invoice_row = factories.add_invoice_row(
            item=self.ticket,
            user=self.alice,
            invoice=self.invoice,
            vat_rate=ZERO_RATE_VAT
        )

        self.assertEqual(invoice_row.total_inc_vat, self.ticket.cost_excl_vat())
