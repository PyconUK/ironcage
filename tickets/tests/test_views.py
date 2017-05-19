from django.test import TestCase

from django.contrib.auth.models import User

from tickets import actions


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
