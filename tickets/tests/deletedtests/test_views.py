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


# class OrderEditTests(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.order = factories.create_unpaid_order_for_self()

#     def test_get(self):
#         self.client.force_login(self.order.purchaser)
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/')
#         self.assertInHTML('<tr><td class="text-center">5 days</td><td class="text-center">£198</td><td class="text-center">£396</td><td class="text-center">£66</td></tr>', rsp.content.decode())
#         self.assertContains(rsp, '<form method="post" id="order-form">')
#         self.assertNotContains(rsp, 'Please create an account to buy a ticket.')

#     def test_get_when_user_has_order_for_self(self):
#         self.client.force_login(self.order.purchaser)
#         factories.create_paid_order_for_self(self.order.purchaser)
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/')
#         self.assertNotContains(rsp, '<input type="radio" name="who" value="self">')
#         self.assertContains(rsp, '<input type="hidden" name="who" value="others">')

#     def test_get_when_user_has_order_but_not_for_self(self):
#         self.client.force_login(self.order.purchaser)
#         factories.create_paid_order_for_others(self.order.purchaser)
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/')
#         self.assertContains(rsp, '<input type="radio" name="who" value="self" checked>')
#         self.assertNotContains(rsp, '<input type="hidden" name="who" value="others">')

#     def test_post_for_self(self):
#         self.client.force_login(self.order.purchaser)
#         form_data = {
#             'who': 'self',
#             'rate': Ticket.CORPORATE,
#             'company_name': 'Sirius Cybernetics Corp.',
#             'company_addr': 'Eadrax, Sirius Tau',
#             'days': ['fri', 'sat', 'sun'],
#             # The formset gets POSTed even when order is only for self
#             'form-TOTAL_FORMS': '2',
#             'form-INITIAL_FORMS': '0',
#             'form-MIN_NUM_FORMS': '1',
#             'form-MAX_NUM_FORMS': '1000',
#             'form-0-email_addr': '',
#             'form-1-email_addr': '',
#         }
#         rsp = self.client.post(f'/tickets/orders/{self.order.id}/edit/', form_data, follow=True)
#         self.assertContains(rsp, 'You are ordering 1 ticket')

#     def test_post_for_others(self):
#         self.client.force_login(self.order.purchaser)
#         form_data = {
#             'who': 'others',
#             'rate': Ticket.CORPORATE,
#             'company_name': 'Sirius Cybernetics Corp.',
#             'company_addr': 'Eadrax, Sirius Tau',
#             'form-TOTAL_FORMS': '2',
#             'form-INITIAL_FORMS': '0',
#             'form-MIN_NUM_FORMS': '1',
#             'form-MAX_NUM_FORMS': '1000',
#             'form-0-email_addr': 'test1@example.com',
#             'form-0-days': ['mon', 'tue'],
#             'form-1-email_addr': 'test2@example.com',
#             'form-1-days': ['sat', 'sun', 'mon'],
#         }
#         rsp = self.client.post(f'/tickets/orders/{self.order.id}/edit/', form_data, follow=True)
#         self.assertContains(rsp, 'You are ordering 2 tickets')

#     def test_post_for_self_and_others(self):
#         self.client.force_login(self.order.purchaser)
#         form_data = {
#             'who': 'self and others',
#             'rate': Ticket.CORPORATE,
#             'company_name': 'Sirius Cybernetics Corp.',
#             'company_addr': 'Eadrax, Sirius Tau',
#             'days': ['fri', 'sat', 'sun'],
#             'form-TOTAL_FORMS': '2',
#             'form-INITIAL_FORMS': '0',
#             'form-MIN_NUM_FORMS': '1',
#             'form-MAX_NUM_FORMS': '1000',
#             'form-0-email_addr': 'test1@example.com',
#             'form-0-days': ['mon', 'tue'],
#             'form-1-email_addr': 'test2@example.com',
#             'form-1-days': ['sat', 'sun', 'mon'],
#         }
#         rsp = self.client.post(f'/tickets/orders/{self.order.id}/edit/', form_data, follow=True)
#         self.assertContains(rsp, 'You are ordering 3 tickets')

#     def test_get_when_not_authenticated(self):
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/')
#         self.assertRedirects(rsp, f'/accounts/login/?next=/tickets/orders/{self.order.id}/edit/')

#     def test_post_when_not_authenticated(self):
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/', follow=True)
#         self.assertRedirects(rsp, f'/accounts/login/?next=/tickets/orders/{self.order.id}/edit/')

#     def test_get_when_not_authorized(self):
#         bob = factories.create_user('Bob')
#         self.client.force_login(bob)
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/', follow=True)
#         self.assertRedirects(rsp, '/')
#         self.assertContains(rsp, 'Only the purchaser of an order can update the order')

#     def test_post_when_not_authorized(self):
#         bob = factories.create_user('Bob')
#         self.client.force_login(bob)
#         rsp = self.client.post(f'/tickets/orders/{self.order.id}/edit/', follow=True)
#         self.assertRedirects(rsp, '/')
#         self.assertContains(rsp, 'Only the purchaser of an order can update the order')

#     def test_get_when_already_paid(self):
#         factories.confirm_order(self.order)
#         self.client.force_login(self.order.purchaser)
#         rsp = self.client.get(f'/tickets/orders/{self.order.id}/edit/', follow=True)
#         self.assertRedirects(rsp, f'/payments/orders/{self.order.id}/')
#         self.assertContains(rsp, 'This order has already been paid')
