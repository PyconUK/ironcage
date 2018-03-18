from django.test import TestCase

from payments.models import STANDARD_RATE_VAT
from payments.tests import factories
from tickets.tests import factories as ticket_factories


class AddInvoiceRowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def test_add_invoice_row_to_invoice(self):
        self.invoice.add_row(self.ticket)

        self.assertEqual(self.invoice.rows.count(), 1)

        invoice_row = self.invoice.rows.all()[0]

        self.assertEqual(invoice_row.invoice_item, self.ticket)
        self.assertEqual(invoice_row.total_ex_vat, self.ticket.cost_excl_vat())
        self.assertTrue(invoice_row.total_ex_vat != 0)
        self.assertEqual(invoice_row.vat_rate, STANDARD_RATE_VAT)

