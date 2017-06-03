import stripe

from django.test import TestCase

from accounts.models import User

from .utils import patched_charge_creation_failure, patched_charge_creation_success

from tickets import actions
from tickets import stripe_integration


class StripeIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')
        cls.order = actions.place_order_for_self(
            alice,
            'individual',
            ['thu', 'fri', 'sat']
        )

    def setUp(self):
        self.order.refresh_from_db()

    def test_create_charge_for_order_with_successful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with patched_charge_creation_success():
            charge = stripe_integration.create_charge_for_order(self.order, token)
        self.assertEqual(charge.id, 'ch_abcdefghijklmnopqurstuvw')

    def test_create_charge_for_order_with_unsuccessful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with self.assertRaises(stripe.error.CardError):
            with patched_charge_creation_failure():
                stripe_integration.create_charge_for_order(self.order, token)
