from datetime import (
    datetime,
    timedelta,
    timezone,
)
from unittest import skip

from django.test import (
    override_settings,
    TestCase,
)

from ironcage.tests import utils
from tickets import actions
from tickets.tests import factories
from tickets.models import TicketInvitation, Ticket


class OrderTests(TestCase):
    def test_for_paid_order_for_self(self):
        # arrange
        order = factories.create_paid_order_for_self()
        self.client.force_login(order.purchaser)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'View your ticket')

    def test_for_paid_order_for_others(self):
        # arrange
        order = factories.create_paid_order_for_others()
        self.client.force_login(order.purchaser)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

    def test_for_paid_order_for_self_and_others(self):
        # arrange
        order = factories.create_paid_order_for_self_and_others()
        self.client.force_login(order.purchaser)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'View your ticket')

    def test_for_unpaid_order(self):
        # arrange
        user = factories.create_user(email_addr='alice@example.com')
        order = factories.create_unpaid_order_for_self(user)
        self.client.force_login(user)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'data-amount="12600"')
        self.assertContains(rsp, 'data-email="alice@example.com"')

    @skip
    def test_for_unpaid_order_for_self_when_already_has_ticket(self):
        # arrange
        user = factories.create_user(email_addr='alice@example.com')
        factories.create_paid_order_for_self(user)
        order = factories.create_unpaid_order_for_self(user)
        self.client.force_login(user)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertRedirects(rsp, f'/payments/orders/{order.id}/edit/')
        self.assertContains(rsp, 'You already have a ticket.  Please amend your order.')

    def test_for_failed_order(self):
        # arrange
        order = factories.create_failed_order()
        self.client.force_login(order.purchaser)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertContains(rsp, 'Payment for this invoice failed')
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

    def test_for_errored_order(self):
        # arrange
        order = factories.create_errored_order()
        self.client.force_login(order.purchaser)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Details of your order')
        self.assertContains(rsp, f'Invoice Number</th>\n        <td>{order.item_id}')
        self.assertContains(rsp, 'There was an error creating your invoice')
        self.assertNotContains(rsp, '<div id="stripe-form">')
        self.assertNotContains(rsp, 'View your ticket')

    def test_when_not_authenticated(self):
        # arrange
        order = factories.create_paid_order_for_self()

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertRedirects(rsp, f'/accounts/login/?next=/payments/orders/{order.id}/')

    def test_when_not_authorized(self):
        # arrange
        order = factories.create_paid_order_for_self()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/', follow=True)

        # assert
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an invoice can view the invoice')


class OrderPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_unpaid_order_for_self()

    def test_stripe_success(self):
        # arrange
        self.client.force_login(self.order.purchaser)

        # act
        with utils.patched_charge_creation_success(self.order.total_pence_inc_vat):
            rsp = self.client.post(
                f'/payments/orders/{self.order.id}/payment/',
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        invoice_date = self.order.created_at.strftime('%B %-d, %Y')

        # assert
        self.assertContains(rsp, 'Payment for this invoice has been received')
        self.assertContains(rsp, f'<th>Date</th>\n        <td>{invoice_date}</td>', html=True)
        self.assertNotContains(rsp, '<div id="stripe-form">')

    def test_stripe_failure(self):
        # arrange
        self.client.force_login(self.order.purchaser)

        # act
        with utils.patched_charge_creation_failure():
            rsp = self.client.post(
                f'/payments/orders/{self.order.id}/payment/',
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )

        # assert
        self.assertContains(rsp, 'Payment for this invoice failed')
        self.assertContains(rsp, '<th>Status</th>\n        <td>Unpaid</td>', html=True)
        self.assertContains(rsp, '<div id="stripe-form">')

    @skip
    def test_when_already_has_ticket(self):
        # arrange
        factories.create_paid_order_for_self(self.order.purchaser)
        self.client.force_login(self.order.purchaser)

        # act
        rsp = self.client.post(
            f'/payments/orders/{self.order.id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )

        # assert
        self.assertRedirects(rsp, f'/tickets/orders/{self.order.id}/edit/')
        self.assertContains(rsp, 'You already have a ticket.  Please amend your order.  Your card has not been charged.')

    def test_when_already_paid(self):
        # arrange
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)

        # act
        rsp = self.client.post(
            f'/payments/orders/{self.order.id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )

        # assert
        self.assertRedirects(rsp, f'/payments/orders/{self.order.id}/')
        self.assertContains(rsp, 'This invoice has already been paid')

    def test_when_not_authenticated(self):
        # arrange

        # act
        rsp = self.client.post(
            f'/payments/orders/{self.order.id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )

        # assert
        self.assertRedirects(rsp, f'/accounts/login/?next=/payments/orders/{self.order.id}/payment/')

    def test_when_not_authorized(self):
        # arrange
        bob = factories.create_user('Bob')
        self.client.force_login(bob)

        # act
        rsp = self.client.post(
            f'/payments/orders/{self.order.id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )

        # assert
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an invoice can pay for the invoice')


class OrderReceiptTests(TestCase):

    def setUp(self):
        self.invoice = factories.create_paid_order_for_self_and_others()

    def test_order_receipt(self):
        # arrange
        self.client.force_login(self.invoice.purchaser)

        invoice_date = self.invoice.created_at.strftime('%B %-d, %Y')

        # act
        rsp = self.client.get(f'/payments/payment/{self.invoice.successful_payment.id}/', follow=True)

        # assert
        self.assertContains(rsp, f'Receipt for PyCon UK 2018')
        self.assertContains(rsp, f'<th>Invoice number</th>\n        <td>{self.invoice.item_id}</td>')
        self.assertContains(rsp, f'<th>Payment number</th>\n        <td>{self.invoice.payments.all()[0].id}</td>')
        self.assertContains(rsp, f'<th>Date</th>\n        <td>{invoice_date}</td>', html=True)
        self.assertContains(rsp, '<th>Total (excl. VAT)</th>\n        <td>&pound;255.00</td>', html=True)
        self.assertContains(rsp, '<th>VAT</th>\n        <td>&pound;51.00</td>', html=True)
        self.assertContains(rsp, '<th>Total (incl. VAT)</th>\n        <td>&pound;306.00</td>', html=True)
        self.assertContains(rsp, '<th>Total received</th>\n        <td>&pound;306.00</td>', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>BEA7</td>
                <td>PyCon UK 2018 Ticket for bob@example.com (Saturday, Sunday)</td>
                <td>1</td>
                <td>&pound;75.00</td>
                <td>20%</td>
                <td>&pound;90.00</td>
            </tr>''', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>50F0</td>
                <td>PyCon UK 2018 Ticket for carol@example.com (Sunday, Monday)</td>
                <td>1</td>
                <td>&pound;75.00</td>
                <td>20%</td>
                <td>&pound;90.00</td>
            </tr>''', html=True)
        self.assertContains(rsp, '''
            <tr>
                <td>2C5E</td>
                <td>PyCon UK 2018 Ticket for Alice (Saturday, Sunday, Monday)</td>
                <td>1</td>
                <td>&pound;105.00</td>
                <td>20%</td>
                <td>&pound;126.00</td>
            </tr>''', html=True)

    def test_when_not_authenticated(self):
        # arrange

        # act
        rsp = self.client.get(f'/payments/payment/{self.invoice.successful_payment.id}/', follow=True)

        # assert
        self.assertRedirects(rsp, f'/accounts/login/?next=/payments/payment/{self.invoice.successful_payment.id}/')

    def test_when_not_authorized(self):
        # arrange
        bob = factories.create_user('Bob')
        self.client.force_login(bob)

        # act
        rsp = self.client.get(f'/payments/payment/{self.invoice.successful_payment.id}/', follow=True)

        # assert
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can view the receipt')

    @skip
    def test_when_already_paid(self):
        # arrange
        bob = factories.create_user('Bob')
        order = factories.create_unpaid_order_for_self(user=bob)
        self.client.force_login(bob)

        # act
        rsp = self.client.get(f'/payments/orders/{order.id}/receipt/', follow=True)

        # assert
        self.assertRedirects(rsp, f'/payments/orders/{order.id}/')
        self.assertContains(rsp, 'This order has not been paid')
