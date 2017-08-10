from django.test import TestCase

from ironcage.tests import utils

from . import factories


class NewOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/children/orders/new/')
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'to buy tickets')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-name': 'Percy Pea',
            'form-0-date_of_birth': '2012-01-01',
            'adult_name': 'Alice Apple',
            'adult_email_addr': 'alice@example.com',
            'adult_phone_number': '07123 456789',
            'accessibility_reqs': '',
            'dietary_reqs': '',
        }
        rsp = self.client.post('/children/orders/new/', form_data, follow=True)
        self.assertContains(rsp, "You are ordering 1 children's day ticket")
        self.assertContains(rsp, '<th>Date</th><td>Unpaid</td>', html=True)
        self.assertContains(rsp, '<td>Percy Pea</td><td>2012-01-01</td>', html=True)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get('/children/orders/new/')
        self.assertNotContains(rsp, '<form method="post" id="order-form">')
        self.assertContains(rsp, 'to buy tickets')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post('/children/orders/new/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class OrderEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_order()

    def setUp(self):
        self.order.refresh_from_db()

    def test_get(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/edit/')
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'to buy tickets')

    def test_post(self):
        self.client.force_login(self.order.purchaser)
        form_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-name': 'Percy Pea',
            'form-0-date_of_birth': '2012-01-01',
            'form-1-name': 'Bertie Bean',
            'form-1-date_of_birth': '',
            'adult_name': 'Alice Apple',
            'adult_email_addr': 'alice@example.com',
            'adult_phone_number': '07123 456789',
            'accessibility_reqs': '',
            'dietary_reqs': '',
        }
        rsp = self.client.post(f'/children/orders/{self.order.order_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, "You are ordering 2 children's day tickets")
        self.assertContains(rsp, '<th>Date</th><td>Unpaid</td>', html=True)
        self.assertContains(rsp, '<td>Percy Pea</td><td>2012-01-01</td>', html=True)
        self.assertContains(rsp, '<td>Bertie Bean</td><td>unknown</td>', html=True)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/children/orders/{self.order.order_id}/edit/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(f'/children/orders/{self.order.order_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/children/orders/{self.order.order_id}/edit/')

    def test_get_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_post_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(f'/children/orders/{self.order.order_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can update the order')

    def test_get_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/children/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')

    def test_post_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(f'/children/orders/{self.order.order_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/children/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')


class OrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_order()

    def test_for_confirmed_order(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/', follow=True)
        self.assertContains(rsp, f"Details of your children's day order ({self.order.order_id})")
        self.assertNotContains(rsp, '<div id="stripe-form">')

    def test_for_pending_order(self):
        self.client.force_login(self.order.purchaser)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/', follow=True)
        self.assertContains(rsp, f"Details of your children's day order ({self.order.order_id})")
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, 'data-amount="500"')
        self.assertContains(rsp, f'data-email="{self.order.purchaser.email_addr}"')

    def test_when_not_authenticated(self):
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/children/orders/{self.order.order_id}/')

    def test_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/children/orders/{self.order.order_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can view the order')


class OrderPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.order = factories.create_pending_order()

    def test_stripe_success(self):
        self.client.force_login(self.order.purchaser)
        with utils.patched_charge_creation_success():
            rsp = self.client.post(
                f'/children/orders/{self.order.order_id}/payment/',
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order has been received')
        self.assertContains(rsp, '<th>Date</th><td>May 21, 2017</td>', html=True)
        self.assertNotContains(rsp, '<div id="stripe-form">')

    def test_stripe_failure(self):
        self.client.force_login(self.order.purchaser)
        with utils.patched_charge_creation_failure():
            rsp = self.client.post(
                f'/children/orders/{self.order.order_id}/payment/',
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order failed (Your card was declined.)')
        self.assertContains(rsp, '<th>Date</th><td>Unpaid</td>', html=True)
        self.assertContains(rsp, '<div id="stripe-form">')

    def test_when_already_paid(self):
        factories.confirm_order(self.order)
        self.client.force_login(self.order.purchaser)
        rsp = self.client.post(
            f'/children/orders/{self.order.order_id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, f'/children/orders/{self.order.order_id}/')
        self.assertContains(rsp, 'This order has already been paid')

    def test_when_not_authenticated(self):
        rsp = self.client.post(
            f'/children/orders/{self.order.order_id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, f'/accounts/login/?next=/children/orders/{self.order.order_id}/payment/')

    def test_when_not_authorized(self):
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(
            f'/children/orders/{self.order.order_id}/payment/',
            {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
            follow=True,
        )
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the purchaser of an order can pay for the order')
