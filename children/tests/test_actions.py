from datetime import date

from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase

from . import factories
from ironcage.tests import utils

from children import actions


class CreatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_create_pending_order(self):
        unconfirmed_details = [
            ['Percy Pea', '2012-01-01'],
        ]

        order = actions.create_pending_order(
            purchaser=self.alice,
            adult_name=self.alice.name,
            adult_phone_number='07123 456789',
            adult_email_addr=self.alice.email_addr,
            accessibility_reqs=None,
            dietary_reqs=None,
            unconfirmed_details=unconfirmed_details,
        )

        self.assertEqual(self.alice.children_orders.count(), 1)

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(
            order.ticket_details(),
            [{'name': 'Percy Pea', 'date_of_birth': '2012-01-01'}]
        )


class UpdatePendingOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_update_pending_order(self):
        order = factories.create_pending_order(self.alice)

        unconfirmed_details = [
            ['Percy Pea', '2012-01-01'],
            ['Bertie Bean', None],
        ]

        actions.update_pending_order(
            order,
            adult_name=self.alice.name,
            adult_phone_number='07123 456789',
            adult_email_addr=self.alice.email_addr,
            accessibility_reqs=None,
            dietary_reqs=None,
            unconfirmed_details=unconfirmed_details,
        )

        self.assertEqual(order.purchaser, self.alice)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Percy Pea', 'date_of_birth': '2012-01-01'},
                {'name': 'Bertie Bean', 'date_of_birth': None},
            ]
        )


class ConfirmOrderTests(TestCase):
    def test_confirm_order(self):
        order = factories.create_pending_order()
        actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)

        self.assertEqual(order.stripe_charge_id, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(order.stripe_charge_created.timestamp(), 1495355163)
        self.assertEqual(order.stripe_charge_failure_reason, '')
        self.assertEqual(order.status, 'successful')

        self.assertEqual(order.purchaser.children_orders.count(), 1)
        self.assertEqual(
            order.ticket_details(),
            [
                {'name': 'Percy Pea', 'date_of_birth': date(2012, 1, 1)},
            ]
        )
        self.assertEqual(len(mail.outbox), 1)


class MarkOrderAsFailed(TestCase):
    def test_mark_order_as_failed(self):
        order = factories.create_pending_order()

        actions.mark_order_as_failed(order, 'There was a problem')

        self.assertEqual(order.stripe_charge_failure_reason, 'There was a problem')
        self.assertEqual(order.status, 'failed')


class ProcessStripeChargeTests(TestCase):
    def setUp(self):
        self.order = factories.create_pending_order()

    def test_process_stripe_charge_success(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_success():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'successful')

    def test_process_stripe_charge_failure(self):
        token = 'tok_ abcdefghijklmnopqurstuvwx'
        with utils.patched_charge_creation_failure():
            actions.process_stripe_charge(self.order, token)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')
