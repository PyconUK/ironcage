from django.test import TestCase

from django.contrib.auth.models import User

from .utils import patched_charge_creation_failure, patched_charge_creation_success

from tickets import actions
from tickets import models
from tickets import stripe_integration


class StripeIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(username='Alice')
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
            stripe_integration.create_charge_for_order(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(self.order.stripe_charge_failure_reason, '')
        self.assertEqual(self.order.status, 'successful')

    def test_create_charge_for_order_with_unsuccessful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with patched_charge_creation_failure():
            stripe_integration.create_charge_for_order(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.stripe_charge_id, '')
        self.assertEqual(self.order.stripe_charge_failure_reason, 'Your card was declined.')
        self.assertEqual(self.order.status, 'failed')

    def test_create_charge_for_order_with_successful_charge_after_unsuccessful_charge(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'

        with patched_charge_creation_failure():
            stripe_integration.create_charge_for_order(self.order, token)

        with patched_charge_creation_success():
            stripe_integration.create_charge_for_order(self.order, token)

        self.order.refresh_from_db()
        self.assertEqual(self.order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(self.order.stripe_charge_failure_reason, '')
        self.assertEqual(self.order.status, 'successful')
