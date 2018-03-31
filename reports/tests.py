from django.test import TestCase

from accounts.tests import factories as accounts_factories
from tickets.tests import factories as tickets_factories

from reports import reports


class ReportsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = accounts_factories.create_staff_user(
            name='Alice',
            email_addr='alice@example.com',
        )
        cls.bob = accounts_factories.create_user(
            name='Bob',
            email_addr='bob@example.com',
        )

    def setUp(self):
        self.client.force_login(self.alice)


class TestIndex(ReportsTestCase):
    def test_get(self):
        rsp = self.client.get('/reports/')
        self.assertEqual(rsp.status_code, 200)
        self.assertContains(rsp, '<li><a href="/reports/attendance-by-day/">Attendance by day</a></li>', html=True)

    def test_get_when_not_staff(self):
        self.client.force_login(self.bob)
        rsp = self.client.get('/reports/', follow=True)
        self.assertContains(rsp, "Your account doesn't have access to this page")
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/')

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/reports/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/')


class TestAttendanceByDayReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tickets_factories.create_ticket(num_days=1)
        tickets_factories.create_ticket(num_days=2, rate='corporate')
        tickets_factories.create_ticket(num_days=3)
        tickets_factories.create_ticket(num_days=4, rate='corporate')
        tickets_factories.create_ticket(num_days=5)

    def test_get_context_data(self):
        report = reports.AttendanceByDayReport()
        expected = {
            'title': 'Attendance by day',
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
            'rows': [
                ['Saturday', 3, 2, 0, 0, 5],
                ['Sunday', 2, 2, 0, 0, 4],
                ['Monday', 2, 1, 0, 0, 3],
                ['Tuesday', 1, 1, 0, 0, 2],
                ['Wednesday', 1, 0, 0, 0, 1],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/attendance-by-day/')
        self.assertEqual(rsp.status_code, 200)

    def test_get_when_not_staff(self):
        self.client.force_login(self.bob)
        rsp = self.client.get('/reports/attendance-by-day/', follow=True)
        self.assertContains(rsp, "Your account doesn't have access to this page")
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/attendance-by-day/')

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/reports/attendance-by-day/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/reports/attendance-by-day/')


class TestTicketSalesReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tickets_factories.create_ticket(num_days=1)
        tickets_factories.create_ticket(num_days=2, rate='corporate')
        tickets_factories.create_ticket(num_days=3)
        tickets_factories.create_ticket(num_days=4, rate='corporate')
        tickets_factories.create_ticket(num_days=5)

    def test_get_context_data(self):
        report = reports.TicketSalesReport()
        expected = {
            'title': 'Ticket sales',
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
            'num_tickets_rows': [
                [1, 1, 0, 0, 0, 1],
                [2, 0, 1, 0, 0, 1],
                [3, 1, 0, 0, 0, 1],
                [4, 0, 1, 0, 0, 1],
                [5, 1, 0, 0, 0, 1],
            ],
            'ticket_cost_rows': [
                [1, '£54', '£0', '£0', '£0', '£54'],
                [2, '£0', '£180', '£0', '£0', '£180'],
                [3, '£126', '£0', '£0', '£0', '£126'],
                [4, '£0', '£324', '£0', '£0', '£324'],
                [5, '£198', '£0', '£0', '£0', '£198'],
            ]
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/ticket-sales/')
        self.assertEqual(rsp.status_code, 200)


class TestOrdersReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.order1 = tickets_factories.create_pending_order_for_self(cls.alice, num_days=1)
        cls.order2 = tickets_factories.create_confirmed_order_for_self(cls.bob, num_days=2)

    def test_get_context_data(self):
        report = reports.OrdersReport()
        links = [{
            'href': f'/reports/tickets/orders/{order.order_id}/',
            'text': order.order_id,
        } for order in [self.order1, self.order2]]
        expected = {
            'title': 'All orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [links[0], 'individual', 'Alice', 'alice@example.com', 1, '£54', 'pending'],
                [links[1], 'individual', 'Bob', 'bob@example.com', 1, '£90', 'successful'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/all-orders/')
        self.assertEqual(rsp.status_code, 200)


class TestUnpaidOrdersReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.order1 = tickets_factories.create_pending_order_for_self(cls.alice, num_days=1)
        tickets_factories.create_confirmed_order_for_self(cls.bob, num_days=2)

    def test_get_context_data(self):
        report = reports.UnpaidOrdersReport()
        link = {
            'href': f'/reports/tickets/orders/{self.order1.order_id}/',
            'text': self.order1.order_id,
        }
        expected = {
            'title': 'Unpaid orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [link, 'individual', 'Alice', 'alice@example.com', 1, '£54', 'pending'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/unpaid-orders/')
        self.assertEqual(rsp.status_code, 200)


class TestTicketsReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ticket1 = tickets_factories.create_ticket(cls.alice)
        order = tickets_factories.create_confirmed_order_for_others(cls.alice)
        cls.ticket2, cls.ticket3 = order.all_tickets()

    def test_get_context_data(self):
        report = reports.TicketsReport()
        links = [{
            'href': f'/reports/tickets/tickets/{ticket.ticket_id}/',
            'text': ticket.ticket_id,
        } for ticket in [self.ticket1, self.ticket2, self.ticket3]]
        expected = {
            'title': 'All tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [links[0], 'individual', 'Alice', 'Saturday, Sunday, Monday', '£126', 'Assigned'],
                [links[1], 'individual', 'bob@example.com', 'Saturday, Sunday', '£90', 'Unclaimed'],
                [links[2], 'individual', 'carol@example.com', 'Sunday, Monday', '£90', 'Unclaimed'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/all-tickets/')
        self.assertEqual(rsp.status_code, 200)


class TestUnclaimedTicketsReport(ReportsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tickets_factories.create_ticket(cls.alice)
        order = tickets_factories.create_confirmed_order_for_others(cls.alice)
        cls.ticket2, cls.ticket3 = order.all_tickets()

    def test_get_context_data(self):
        report = reports.UnclaimedTicketsReport()
        links = [{
            'href': f'/reports/tickets/tickets/{ticket.ticket_id}/',
            'text': ticket.ticket_id,
        } for ticket in [self.ticket2, self.ticket3]]
        expected = {
            'title': 'Unclaimed tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [links[0], 'individual', 'bob@example.com', 'Saturday, Sunday', '£90', 'Unclaimed'],
                [links[1], 'individual', 'carol@example.com', 'Sunday, Monday', '£90', 'Unclaimed'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/unclaimed-tickets/')
        self.assertEqual(rsp.status_code, 200)
