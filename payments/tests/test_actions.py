from unittest.mock import patch

from django.test import TestCase

from payments import actions
from payments.tests import factories


class CreateInvoiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_create_invoice(self):
        invoice = actions._create_invoice(
            self.alice,
            'Alice',
            False
        )

        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.invoice_to, 'Alice')
        self.assertEqual(invoice.is_credit, False)
        self.assertEqual(invoice.total, 0)

    def test_create_invoice_as_credit(self):
        invoice = actions._create_invoice(
            self.alice,
            'Alice',
            True
        )

        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.invoice_to, 'Alice')
        self.assertEqual(invoice.is_credit, True)
        self.assertEqual(invoice.total, 0)

    def test_create_invoice_invoiced_to_company(self):
        invoice = actions._create_invoice(
            self.alice,
            'My Company Limited',
            False
        )

        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.invoice_to, 'My Company Limited')
        self.assertEqual(invoice.is_credit, False)
        self.assertEqual(invoice.total, 0)

    def test_create_invoice_change_purchaser_name_does_not_change_invoice_to(self):
        invoice = actions._create_invoice(
            self.alice,
            'Alice',
            False
        )

        self.alice.name = 'Bob'
        self.alice.save()

        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.purchaser.name, 'Bob')
        self.assertEqual(invoice.invoice_to, 'Alice')
        self.assertEqual(invoice.is_credit, False)
        self.assertEqual(invoice.total, 0)


class CreateNewInvoiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    @patch('payments.actions._create_invoice')
    def test_create_new_invoice(self, _create_invoice):
        actions.create_new_invoice(
            self.alice,
            'Alice'
        )

        _create_invoice.assert_called_once_with(
            self.alice, 'Alice', is_credit=False
        )

    @patch('payments.actions._create_invoice')
    def test_create_new_invoice_invoiced_to_company(self, _create_invoice):
        actions.create_new_invoice(
            self.alice,
            'My Company Limited'
        )

        _create_invoice.assert_called_once_with(
            self.alice, 'My Company Limited', is_credit=False
        )


class CreateNewCreditNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    @patch('payments.actions._create_invoice')
    def test_create_new_credit_note(self, _create_invoice):
        actions.create_new_credit_note(
            self.alice,
            'Alice'
        )

        _create_invoice.assert_called_once_with(
            self.alice, 'Alice', is_credit=True
        )

    @patch('payments.actions._create_invoice')
    def test_create_new_credit_note_invoiced_to_company(self, _create_invoice):
        actions.create_new_credit_note(
            self.alice,
            'My Company Limited'
        )

        _create_invoice.assert_called_once_with(
            self.alice, 'My Company Limited', is_credit=True
        )
