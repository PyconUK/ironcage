from django.test import TestCase

from accounts.tests import factories as account_factories
from tickets.tests import factories as ticket_factories


class IndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = account_factories.create_user()

    def setUp(self):
        self.client.force_login(self.alice)

    def test_when_not_signed_in(self):
        self.client.logout()

        rsp = self.client.get('/')
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order conference tickets</a>', html=True)
        self.assertNotContains(rsp, '<a href="/profile/">Update your profile</a>', html=True)

    def test_when_has_ticket(self):
        ticket = ticket_factories.create_ticket(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, 'You have a ticket for Thursday, Friday, Saturday')
        self.assertContains(rsp, f'<a href="/tickets/tickets/{ticket.ticket_id}/">View your conference ticket</a>', html=True)
        self.assertContains(rsp, '<a href="/profile/">Update your profile</a>', html=True)

    def test_when_has_ticket_and_full_profile(self):
        user = account_factories.create_user_with_full_profile()
        ticket_factories.create_ticket(user)
        self.client.force_login(user)

        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'Update your profile')

    def test_when_has_no_ticket(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'You have a ticket')
        self.assertNotContains(rsp, 'View your conference ticket')
        self.assertNotContains(rsp, 'Update your profile')

    def test_when_has_order(self):
        order = ticket_factories.create_confirmed_order_for_others(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, f'<a href="/tickets/orders/{order.order_id}/">View your order</a>', html=True)
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order more conference tickets</a>', html=True)

    def test_when_has_no_order(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'View your order')
        self.assertNotContains(rsp, 'Order more conference tickets')

    def test_when_has_multiple_orders(self):
        order1 = ticket_factories.create_confirmed_order_for_self(self.alice)
        order2 = ticket_factories.create_confirmed_order_for_others(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, f'<a href="/tickets/orders/{order1.order_id}/">View order {order1.order_id}</a>', html=True)
        self.assertContains(rsp, f'<a href="/tickets/orders/{order2.order_id}/">View order {order2.order_id}</a>', html=True)
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order more conference tickets</a>', html=True)
