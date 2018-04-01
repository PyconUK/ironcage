import stripe

from django.test import TestCase

from ironcage.tests import utils

from payments import stripe_integration
from payments.tests import factories
from tickets.tests import factories as ticket_factories


class StripeIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = ticket_factories.create_unpaid_order_for_self()
        cls.alice = factories.create_user()
        cls.ticket = ticket_factories.create_ticket(cls.alice)
        cls.invoice = factories.create_invoice(cls.alice)

    def setUp(self):
        self.order.refresh_from_db()

    def test_create_charge_for_invoice_with_successful_charge(self):
        # arrange
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        # act
        with utils.patched_charge_creation_success(self.invoice.total_pence_inc_vat):
            charge = stripe_integration.create_charge_for_invoice(self.invoice, token)
        self.assertEqual(charge.id, 'ch_abcdefghijklmnopqurstuvw')

    def test_create_charge_for_invoice_with_unsuccessful_charge(self):
        # arrange
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        # assert
        with self.assertRaises(stripe.error.CardError):
            # act
            with utils.patched_charge_creation_failure():
                stripe_integration.create_charge_for_invoice(self.invoice, token)

    def test_refund_charge(self):
        # arrange

        # act
        with utils.patched_refund_creation_expected() as mock:
            stripe_integration.refund_charge('ch_abcdefghijklmnopqurstuvw')

        # assert
        mock.assert_called_with(charge='ch_abcdefghijklmnopqurstuvw')
