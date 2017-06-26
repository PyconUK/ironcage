import stripe

from django.test import TestCase

from . import factories
from . import utils

from tickets import stripe_integration


class StripeIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_order_for_self()

    def setUp(self):
        self.order.refresh_from_db()

    def test_create_charge_for_order_with_successful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_success():
            charge = stripe_integration.create_charge_for_order(self.order, token)
        self.assertEqual(charge.id, 'ch_abcdefghijklmnopqurstuvw')

    def test_create_charge_for_order_with_unsuccessful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with self.assertRaises(stripe.error.CardError):
            with utils.patched_charge_creation_failure():
                stripe_integration.create_charge_for_order(self.order, token)

    def test_refund_charge(self):
        with utils.patched_refund_creation_expected() as mock:
            stripe_integration.refund_charge('ch_abcdefghijklmnopqurstuvw')
        mock.assert_called_with(charge='ch_abcdefghijklmnopqurstuvw')
