from django.test import TestCase

from django.core.exceptions import ValidationError

from payments.models import (
    InvoiceHasPaymentsException,
    ItemNotOnInvoiceException,
    STANDARD_RATE_VAT,
    ZERO_RATE_VAT,
)
from payments.tests import factories
from tickets.tests import factories as ticket_factories



class InvoiceVatCalculationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)
        cls.invoice.add_item(cls.ticket)

    def test_vat_calculated_correctly(self):
        # arrange

        # act

        # assert
        self.assertEqual(self.invoice.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(self.invoice.total_vat, self.ticket.cost_excl_vat() * (STANDARD_RATE_VAT / 100))
        self.assertEqual(self.invoice.total_inc_vat, self.ticket.cost_incl_vat())


class AddInvoiceRowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def test_add_invoice_row_to_invoice(self):
        # arrange

        # act
        invoice_row = self.invoice.add_item(self.ticket)

        # assert
        self.assertEqual(self.invoice.rows.count(), 1)

        self.assertEqual(invoice_row.item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, STANDARD_RATE_VAT)

        self.assertEqual(self.invoice.total_inc_vat, invoice_row.total_inc_vat)

    def test_add_invoice_row_to_invoice_zero_vat(self):
        # arrange

        # act
        invoice_row = self.invoice.add_item(self.ticket, ZERO_RATE_VAT)

        # assert
        self.assertEqual(self.invoice.rows.count(), 1)

        self.assertEqual(invoice_row.item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, ZERO_RATE_VAT)

        self.assertEqual(self.invoice.total_inc_vat, invoice_row.total_inc_vat)

    def test_add_same_item_multiple_times_to_invoice_fails(self):
        # arrange
        self.invoice.add_item(self.ticket)

        # assert
        with self.assertRaises(ValidationError):
            # act
            self.invoice.add_item(self.ticket)

    def test_add_two_items_to_invoice(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_incl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.invoice.add_item(self.ticket)
        self.invoice.add_item(ticket_2)

        # assert
        self.assertEqual(self.invoice.rows.count(), 2)
        self.assertEqual(self.invoice.total_inc_vat, total_ticket_cost)

    def test_add_two_items_to_invoice_different_vat_rates(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_excl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.invoice.add_item(self.ticket)
        self.invoice.add_item(ticket_2, ZERO_RATE_VAT)

        # assert
        self.assertEqual(self.invoice.rows.count(), 2)
        self.assertEqual(self.invoice.total_inc_vat, total_ticket_cost)

    def test_add_invoice_row_to_invoice_with_payment_fails(self):
        # arrange
        self.invoice.add_item(self.ticket)
        factories.make_payment(self.invoice)

        ticket_2 = ticket_factories.create_ticket()

        # assert
        with self.assertRaises(InvoiceHasPaymentsException):
            # act
            self.invoice.add_item(ticket_2)


class AddCreditNoteRowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)
        cls.invoice.add_item(cls.ticket)
        cls.credit_note = factories.create_credit_note(cls.alice, cls.invoice)

    def test_add_invoice_row_to_credit_note(self):
        # arrange

        # act
        invoice_row = self.credit_note.add_item(self.ticket)

        # assert
        self.assertEqual(self.credit_note.rows.count(), 1)

        self.assertEqual(invoice_row.item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertEqual(invoice_row.vat_rate, STANDARD_RATE_VAT)

        self.assertEqual(self.credit_note.total_inc_vat, -invoice_row.total_inc_vat)

    def test_add_two_items_to_credit_note(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)

        ticket_1_price = self.ticket.cost_incl_vat()
        ticket_2_price = ticket_2.cost_incl_vat()

        total_ticket_cost = ticket_1_price + ticket_2_price

        # act
        self.credit_note.add_item(self.ticket)
        self.credit_note.add_item(ticket_2)

        # assert
        self.assertEqual(self.credit_note.rows.count(), 2)
        self.assertEqual(self.credit_note.total_inc_vat, -total_ticket_cost)


class InvoiceRowIncVatTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def test_inc_standard_vat(self):
        # arrange

        # act
        invoice_row = factories.add_invoice_item(
            item=self.ticket,
            user=self.alice,
            invoice=self.invoice
        )

        # assert
        self.assertEqual(invoice_row.total_inc_vat, self.ticket.cost_incl_vat())

    def test_inc_zero_vat(self):
        # arrange

        # act
        invoice_row = factories.add_invoice_item(
            item=self.ticket,
            user=self.alice,
            invoice=self.invoice,
            vat_rate=ZERO_RATE_VAT
        )

        # assert
        self.assertEqual(invoice_row.total_inc_vat, self.ticket.cost_excl_vat())


class DeleteInvoiceRowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)
        cls.invoice_row = cls.invoice.add_item(cls.ticket)

    def test_delete_invoice_row_from_invoice(self):
        # arrange

        # act
        self.invoice.delete_item(self.ticket)

        self.invoice.refresh_from_db()

        # assert
        self.assertEqual(self.invoice.rows.count(), 0)
        self.assertEqual(self.invoice.total_inc_vat, 0)

    def test_delete_one_of_two_rows_from_invoice(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)
        self.invoice.add_item(ticket_2)

        # act
        self.invoice.delete_item(self.ticket)

        self.invoice.refresh_from_db()

        # assert
        self.assertEqual(self.invoice.rows.count(), 1)
        self.assertEqual(self.invoice.total_inc_vat, ticket_2.cost_incl_vat())

    def test_delete_two_rows_from_two_row_invoice(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)
        self.invoice.add_item(ticket_2)

        # act
        self.invoice.delete_item(self.ticket)
        self.invoice.delete_item(ticket_2)

        self.invoice.refresh_from_db()

        # assert
        self.assertEqual(self.invoice.rows.count(), 0)
        self.assertEqual(self.invoice.total_inc_vat, 0)

    def test_delete_item_from_invoice_with_payment_fails(self):
        # arrange
        factories.make_payment(self.invoice)

        # assert
        with self.assertRaises(InvoiceHasPaymentsException):
            # act
            self.invoice.delete_item(self.ticket)

    def test_delete_item_not_on_invoice_fails(self):
        # arrange
        ticket_2 = ticket_factories.create_ticket(num_days=5)

        # assert
        with self.assertRaises(ItemNotOnInvoiceException):
            # act
            self.invoice.delete_item(ticket_2)
