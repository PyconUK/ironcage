from django.test import TestCase

from django.contrib.auth.models import User

from tickets import actions
from tickets.models import TicketInvitation


class NewOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username='Alice')

    def setUp(self):
        self.client.force_login(self.alice)

    def test_new_order_for_self(self):
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

    def test_new_order_for_others(self):
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

    def test_new_order_for_self_and_others(self):
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
