from django.test import TestCase

from django.contrib.auth.models import User

from .utils import patched_charge_creation_failure, patched_charge_creation_success

from tickets import actions
from tickets.models import TicketInvitation


class NewOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='Alice')

    def setUp(self):
        self.client.force_login(self.alice)

    def test_get_new_order(self):
        rsp = self.client.get('/tickets/orders/new/')
        self.assertInHTML('<tr><td>5 days</td><td>£138</td><td>£276</td></tr>', rsp.content.decode())

    def test_post_new_order_for_self(self):
        form_data = {
            'who': 'self',
            'rate': 'individual',
            'days': ['thu', 'fri', 'sat'],
            # The formset gets POSTed even when order is only for self
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': '',
            'form-1-email_addr': '',
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You have ordered 1 ticket(s)')

    def test_post_new_order_for_others(self):
        form_data = {
            'who': 'others',
            'rate': 'individual',
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['sat', 'sun', 'mon'],
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You have ordered 2 ticket(s)')

    def test_post_new_order_for_self_and_others(self):
        form_data = {
            'who': 'self and others',
            'rate': 'individual',
            'days': ['thu', 'fri', 'sat'],
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['sat', 'sun', 'mon'],
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You have ordered 3 ticket(s)')


class OrderPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='Alice')
        cls.order = actions.place_order_for_self_and_others(
            cls.alice,
            'individual',
            ['thu', 'fri', 'sat'],
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

    def setUp(self):
        self.client.force_login(self.alice)
        self.order.refresh_from_db()

    def test_order_payment_success(self):
        with patched_charge_creation_success():
            rsp = self.client.post(
                f'/tickets/orders/{self.order.order_id}/payment/',
                {'stripeToken': 'tok_ abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order has been received')
        self.assertNotContains(rsp, '<div id="stripe-form">')

    def test_order_payment_failure(self):
        with patched_charge_creation_failure():
            rsp = self.client.post(
                f'/tickets/orders/{self.order.order_id}/payment/',
                {'stripeToken': 'tok_ abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this order failed (Your card was declined.)')
        self.assertContains(rsp, '<div id="stripe-form">')


class TicketInvitationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(username='Alice')
        actions.place_order_for_others(
            alice,
            'individual',
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )
        cls.invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        cls.bob = User.objects.create_user(username='Bob')

    def setUp(self):
        self.client.force_login(self.bob)

    def test_ticket_invitation_for_unclaimed_invitation(self):
        rsp = self.client.get(f'/tickets/invitations/{self.invitation.token}/', follow=True)
        self.assertContains(rsp, 'Details of your ticket (9A19)')

    def test_ticket_invitation_for_claimed_invitation(self):
        actions.claim_ticket_invitation(self.bob, self.invitation)
        rsp = self.client.get(f'/tickets/invitations/{self.invitation.token}/', follow=True)
        self.assertContains(rsp, 'Details of your ticket (9A19)')
