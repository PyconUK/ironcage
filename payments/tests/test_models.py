from django.test import TestCase

from payments.models import STANDARD_RATE_VAT, ZERO_RATE_VAT
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
