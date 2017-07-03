from django.test import TestCase

from accounts.tests import factories as accounts_factories
from tickets.tests import factories as tickets_factories

from reports import views


class ReportsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = accounts_factories.create_user(
            name='Alice',
            email_addr='alice@example.com',
            is_staff=True
        )
        cls.bob = accounts_factories.create_user(
            name='Bob',
            email_addr='bob@example.com',
            is_staff=False
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
        report = views.AttendanceByDayReport()
        expected = {
            'title': 'Attendance by day',
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Education rate', 'Total'],
            'rows': [
                ['Thursday', 3, 2, 0, 5],
                ['Friday', 2, 2, 0, 4],
                ['Saturday', 2, 1, 0, 3],
                ['Sunday', 1, 1, 0, 2],
                ['Monday', 1, 0, 0, 1],
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
        report = views.TicketSalesReport()
        expected = {
            'title': 'Ticket sales',
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Education rate', 'Total'],
            'num_tickets_rows': [
                [1, 1, 0, 0, 1],
                [2, 0, 1, 0, 1],
                [3, 1, 0, 0, 1],
                [4, 0, 1, 0, 1],
                [5, 1, 0, 0, 1],
            ],
            'ticket_cost_rows': [
                [1, '£54', '£0', '£0', '£54'],
                [2, '£0', '£180', '£0', '£180'],
                [3, '£126', '£0', '£0', '£126'],
                [4, '£0', '£324', '£0', '£324'],
                [5, '£198', '£0', '£0', '£198'],
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
        report = views.OrdersReport()
        expected = {
            'title': 'All orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.order1.order_id, 'individual', 'Alice', 'alice@example.com', 1, '£54', 'pending'],
                [self.order2.order_id, 'individual', 'Bob', 'bob@example.com', 1, '£90', 'successful'],
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
        report = views.UnpaidOrdersReport()
        expected = {
            'title': 'Unpaid orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.order1.order_id, 'individual', 'Alice', 'alice@example.com', 1, '£54', 'pending'],
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
        report = views.TicketsReport()
        expected = {
            'title': 'All tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.ticket1.ticket_id, 'individual', 'Alice', 'Thursday, Friday, Saturday', '£126', 'Assigned'],
                [self.ticket2.ticket_id, 'individual', 'bob@example.com', 'Friday, Saturday', '£90', 'Unclaimed'],
                [self.ticket3.ticket_id, 'individual', 'carol@example.com', 'Saturday, Sunday', '£90', 'Unclaimed'],
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
        report = views.UnclaimedTicketsReport()
        expected = {
            'title': 'Unclaimed tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.ticket2.ticket_id, 'individual', 'bob@example.com', 'Friday, Saturday', '£90', 'Unclaimed'],
                [self.ticket3.ticket_id, 'individual', 'carol@example.com', 'Saturday, Sunday', '£90', 'Unclaimed'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/unclaimed-tickets/')
        self.assertEqual(rsp.status_code, 200)
