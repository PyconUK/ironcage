from datetime import datetime
from unittest.mock import patch, MagicMock
from unittest import skip

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db.utils import IntegrityError

from ironcage.tests import utils
from payments import actions
from payments.exceptions import InvoiceAlreadyPaidException
from payments.models import (
    CreditNote,
    Invoice,
    Payment,
)
from payments.tests import factories
from tickets.tests import factories as ticket_factories


class CreateNewInvoiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_create_new_invoice(self):
        # arrange

        # act
        invoice = actions.create_new_invoice(
            self.alice
        )

        # assert
        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.company_name, None)
        self.assertEqual(invoice.company_addr, None)

        self.assertEqual(invoice.total_ex_vat, 0)
        self.assertEqual(invoice.total_vat, 0)
        self.assertEqual(invoice.total_inc_vat, 0)

        self.assertTrue(isinstance(invoice, Invoice))

    def test_create_new_invoice_invoiced_to_company(self):
        # arrange

        # act
        invoice = actions.create_new_invoice(
            self.alice,
            'My Company Limited',
            'My Company House, My Company Lane, Companyland, MY1 1CO',
        )

        # assert
        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.company_name, 'My Company Limited')
        self.assertEqual(invoice.company_addr, 'My Company House, My Company Lane, Companyland, MY1 1CO')

        self.assertEqual(invoice.total_ex_vat, 0)
        self.assertEqual(invoice.total_vat, 0)
        self.assertEqual(invoice.total_inc_vat, 0)

        self.assertTrue(isinstance(invoice, Invoice))

    def test_create_new_invoice_invoiced_to_company_but_only_name_provided(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            actions.create_new_invoice(
                self.alice,
                'My Company Limited',
            )

        # assert
        self.assertEqual(self.alice.invoices.count(), 0)

    def test_create_new_invoice_invoiced_to_company_but_only_address_provided(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            actions.create_new_invoice(
                self.alice,
                company_addr='My Company House, My Company Lane, Companyland, MY1 1CO',
            )

        # assert
        self.assertEqual(self.alice.invoices.count(), 0)

    def test_create_invoice_change_purchaser_name_does_not_change_invoice(self):
        # arrange
        invoice = actions.create_new_invoice(
            self.alice,
            'My Company Limited',
            'My Company House, My Company Lane, Companyland, MY1 1CO',
        )

        # act
        self.alice.name = 'Bob'
        self.alice.save()

        # assert
        self.assertEqual(self.alice.invoices.count(), 1)

        self.assertEqual(invoice.purchaser, self.alice)
        self.assertEqual(invoice.purchaser.name, 'Bob')
        self.assertEqual(invoice.company_name, 'My Company Limited')
        self.assertEqual(invoice.company_addr, 'My Company House, My Company Lane, Companyland, MY1 1CO')


class CreateNewCreditNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.invoice = factories.create_invoice()
        cls.invoice_with_company = factories.create_invoice(
            cls.alice,
            'My Company Limited',
            'My Company House, My Company Lane, Companyland, MY1 1CO',
        )

    def test_create_new_credit_note_requires_invoice_and_reason(self):
        # arrange

        # assert
        with self.assertRaises(TypeError):
            # act
            actions.create_new_credit_note(
                self.alice,
            )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 0)

    def test_create_new_credit_note_must_have_valid_reason(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            actions.create_new_credit_note(
                self.alice,
                self.invoice,
                'Not a valid reason'
            )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 0)

    def test_create_new_credit_note(self):
        # arrange

        # act
        credit_note = actions.create_new_credit_note(
            self.alice,
            self.invoice,
            CreditNote.CREATED_BY_MISTAKE,
        )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 1)

        self.assertEqual(credit_note.purchaser, self.alice)
        self.assertEqual(credit_note.invoice, self.invoice)
        self.assertEqual(credit_note.reason, CreditNote.CREATED_BY_MISTAKE)
        self.assertEqual(credit_note.company_name, None)
        self.assertEqual(credit_note.company_addr, None)

        self.assertEqual(credit_note.total_ex_vat, 0)
        self.assertEqual(credit_note.total_vat, 0)
        self.assertEqual(credit_note.total_inc_vat, 0)

        self.assertTrue(isinstance(credit_note, CreditNote))

    def test_create_new_credit_note_invoiced_to_company(self):
        # arrange

        # act
        credit_note = actions.create_new_credit_note(
            self.alice,
            self.invoice,
            CreditNote.CREATED_BY_MISTAKE,
            'My Company Limited',
            'My Company House, My Company Lane, Companyland, MY1 1CO',
        )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 1)

        self.assertEqual(credit_note.purchaser, self.alice)
        self.assertEqual(credit_note.invoice, self.invoice)
        self.assertEqual(credit_note.reason, CreditNote.CREATED_BY_MISTAKE)
        self.assertEqual(credit_note.company_name, 'My Company Limited')
        self.assertEqual(credit_note.company_addr, 'My Company House, My Company Lane, Companyland, MY1 1CO')

        self.assertEqual(credit_note.total_ex_vat, 0)
        self.assertEqual(credit_note.total_vat, 0)
        self.assertEqual(credit_note.total_inc_vat, 0)

        self.assertTrue(isinstance(credit_note, CreditNote))

    def test_create_new_credit_note_invoiced_to_company_but_only_name_provided(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            actions.create_new_credit_note(
                self.alice,
                self.invoice,
                CreditNote.CREATED_BY_MISTAKE,
                'My Company Limited',
            )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 0)

    def test_create_new_credit_note_invoiced_to_company_but_only_address_provided(self):
        # arrange

        # assert
        with self.assertRaises(ValidationError):
            # act
            actions.create_new_credit_note(
                self.alice,
                self.invoice,
                CreditNote.CREATED_BY_MISTAKE,
                company_addr='My Company House, My Company Lane, Companyland, MY1 1CO',
            )

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 0)

    def test_create_invoice_change_purchaser_name_does_not_change_invoice(self):
        # arrange
        credit_note = actions.create_new_credit_note(
            self.alice,
            self.invoice,
            CreditNote.CREATED_BY_MISTAKE,
            'My Company Limited',
            'My Company House, My Company Lane, Companyland, MY1 1CO',
        )

        # act
        self.alice.name = 'Bob'
        self.alice.save()

        # assert
        self.assertEqual(self.alice.creditnotes.count(), 1)

        self.assertEqual(credit_note.purchaser, self.alice)
        self.assertEqual(credit_note.purchaser.name, 'Bob')
        self.assertEqual(credit_note.company_name, 'My Company Limited')
        self.assertEqual(credit_note.company_addr, 'My Company House, My Company Lane, Companyland, MY1 1CO')


class ConfirmInvoiceTests(TestCase):
    pass


class MarkPaymentAsFailedTests(TestCase):

    def setUp(self):
        self.invoice = ticket_factories.create_unpaid_order_for_self()

    def test_create_failed_payment(self):
        # arrange

        # act
        payment = actions.create_failed_payment(self.invoice, 'Uh oh', 'ch_qwerty')

        # assert
        self.assertEqual(payment.invoice, self.invoice)
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.FAILED)
        self.assertEqual(payment.charge_failure_reason, 'Uh oh')
        self.assertEqual(payment.charge_id, 'ch_qwerty')
        self.assertEqual(payment.amount, 0)

        self.assertIsNone(self.invoice.successful_payment)


class MarkPaymentAsErroredAfterChargeTests(TestCase):

    def setUp(self):
        self.invoice = ticket_factories.create_unpaid_order_for_self()

    def test_create_errored_after_charge_payment(self):
        # arrange

        # act
        payment = actions.create_errored_after_charge_payment(self.invoice, 'ch_qwerty', self.invoice.total_pence_inc_vat)

        # assert
        self.assertEqual(payment.invoice, self.invoice)
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.ERRORED)
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.charge_id, 'ch_qwerty')
        self.assertEqual(payment.amount, self.invoice.total_inc_vat)

        self.assertIsNone(self.invoice.successful_payment)


class MarkPaymentAsSuccessfulTests(TestCase):

    def setUp(self):
        self.invoice = ticket_factories.create_unpaid_order_for_self()

    def test_create_successful_payment(self):
        # arrange

        # act
        payment = actions.create_successful_payment(self.invoice, 'ch_qwerty', self.invoice.total_pence_inc_vat)

        # assert
        self.assertEqual(payment.invoice, self.invoice)
        self.assertEqual(payment.method, Payment.STRIPE)
        self.assertEqual(payment.status, Payment.SUCCESSFUL)
        self.assertEqual(payment.charge_failure_reason, '')
        self.assertEqual(payment.charge_id, 'ch_qwerty')
        self.assertEqual(payment.amount, self.invoice.total_inc_vat)

        self.assertIsNotNone(self.invoice.successful_payment)


class PayInvoiceByStripeTests(TestCase):

    def setUp(self):
        self.invoice = ticket_factories.create_unpaid_order_for_self()

    @patch('payments.actions.create_successful_payment')
    @patch('payments.actions.confirm_invoice')
    def test_pay_invoice(self, confirm, successful):
        # arrange

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        # assert
        successful.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', self.invoice.total_pence_inc_vat)
        confirm.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', utils.STRIPE_CHARGE_CREATE_TIME)

    def test_pay_invoice_already_paid_fails(self):
        # arrange
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        # assert
        with self.assertRaises(InvoiceAlreadyPaidException):
            # act
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

    @patch('payments.actions.create_successful_payment')
    @patch('payments.actions.create_failed_payment')
    def test_pay_invoice_with_unsuccessful_payment_does_not_mark_as_successful(self, failed, successful):
        # arrange

        # act
        with utils.patched_charge_creation_failure():
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        # assert
        failed.assert_called_once_with(self.invoice, 'Your card was declined.', 'ch_qwerty')
        successful.assert_not_called()

    @patch('payments.actions.create_successful_payment')
    @patch('payments.actions.confirm_invoice')
    def test_pay_invoice_with_previous_unsuccessful_payment_passes(self, confirm, successful):
        # arrange
        with utils.patched_charge_creation_failure():
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        failed_patch = patch('payments.actions.create_failed_payment')
        failed = failed_patch.start()

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        # assert
        successful.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', self.invoice.total_pence_inc_vat)
        confirm.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', utils.STRIPE_CHARGE_CREATE_TIME)
        failed.assert_not_called()

        failed_patch.stop()

    @patch('payments.actions.create_successful_payment', side_effect=IntegrityError)
    @patch('payments.actions.create_errored_after_charge_payment')
    @patch('payments.actions.confirm_invoice')
    @patch('payments.actions.refund_charge')
    def test_pay_invoice_errors_starts_refund_and_marks_as_errored(self, refund, confirm, errored, successful):
        # arrange

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            actions.pay_invoice_by_stripe(self.invoice, 'tok_ abcdefghijklmnopqurstuvwx')

        # assert
        successful.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', self.invoice.total_pence_inc_vat)
        errored.assert_called_once_with(self.invoice, 'ch_abcdefghijklmnopqurstuvw', self.invoice.total_pence_inc_vat)
        refund.assert_called_once_with('ch_abcdefghijklmnopqurstuvw')
        confirm.assert_not_called()


class ProcessStripeChargeTests(TestCase):

    def setUp(self):
        self.invoice = ticket_factories.create_unpaid_order_for_self()

    def test_process_stripe_charge_success(self):
        # arrange
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            payment = actions.pay_invoice_by_stripe(self.invoice, token)

        # assert
        self.assertEqual(payment.status, Payment.SUCCESSFUL)

    def test_process_stripe_charge_failure(self):
        # arrange
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        # act
        with utils.patched_charge_creation_failure():
            payment = actions.pay_invoice_by_stripe(self.invoice, token)

        # assert
        self.assertEqual(payment.status, Payment.FAILED)

    @skip
    def test_process_stripe_charge_error_after_charge(self):
        # arrange
        ticket_factories.create_paid_order_for_self(self.invoice.purchaser)
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat), utils.patched_refund_creation_expected():
            payment = actions.pay_invoice_by_stripe(self.invoice, token)

        self.invoice.refresh_from_db()

        # assert
        self.assertEqual(payment.status, Payment.ERRORED)
        self.assertEqual(payment.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')


