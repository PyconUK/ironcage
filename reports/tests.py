from django.test import TestCase

from tickets.tests import factories as tickets_factories

from reports import views


class TestIndex(TestCase):
    def test_get(self):
        rsp = self.client.get('/reports/')
        self.assertEqual(rsp.status_code, 200)
        self.assertContains(rsp, '<li><a href="/reports/attendance-by-day/">Attendance by day</a></li>', html=True)


class TestAttendanceByDayReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = tickets_factories.create_user()
        tickets_factories.create_ticket(user, num_days=1)
        tickets_factories.create_ticket(user, num_days=2, rate='corporate')
        tickets_factories.create_ticket(user, num_days=3)
        tickets_factories.create_ticket(user, num_days=4, rate='corporate')
        tickets_factories.create_ticket(user, num_days=5)

    def test_get_context_data(self):
        report = views.AttendanceByDayReport()
        expected = {
            'title': 'Attendance by day',
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Total'],
            'rows': [
                ['Thursday', 3, 2, 5],
                ['Friday', 2, 2, 4],
                ['Saturday', 2, 1, 3],
                ['Sunday', 1, 1, 2],
                ['Monday', 1, 0, 1],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/attendance-by-day/')
        self.assertEqual(rsp.status_code, 200)


class TestTicketSalesReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = tickets_factories.create_user()
        tickets_factories.create_ticket(user, num_days=1)
        tickets_factories.create_ticket(user, num_days=2, rate='corporate')
        tickets_factories.create_ticket(user, num_days=3)
        tickets_factories.create_ticket(user, num_days=4, rate='corporate')
        tickets_factories.create_ticket(user, num_days=5)

    def test_get_context_data(self):
        report = views.TicketSalesReport()
        expected = {
            'title': 'Ticket sales',
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Total'],
            'num_tickets_rows': [
                [1, 1, 0, 1],
                [2, 0, 1, 1],
                [3, 1, 0, 1],
                [4, 0, 1, 1],
                [5, 1, 0, 1],
            ],
            'ticket_cost_rows': [
                [1, '£42', '£0', '£42'],
                [2, '£0', '£132', '£132'],
                [3, '£90', '£0', '£90'],
                [4, '£0', '£228', '£228'],
                [5, '£138', '£0', '£138'],
            ]
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/ticket-sales/')
        self.assertEqual(rsp.status_code, 200)


class TestOrdersReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = tickets_factories.create_user('Alice')
        bob = tickets_factories.create_user('Bob')
        cls.order1 = tickets_factories.create_pending_order_for_self(alice, num_days=1)
        cls.order2 = tickets_factories.create_confirmed_order_for_self(bob, num_days=2)

    def test_get_context_data(self):
        report = views.OrdersReport()
        expected = {
            'title': 'All orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.order1.order_id, 'individual', 'Alice', 'alice@example.com', 1, '£42', 'pending'],
                [self.order2.order_id, 'individual', 'Bob', 'bob@example.com', 1, '£66', 'successful'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/all-orders/')
        self.assertEqual(rsp.status_code, 200)


class TestUnpaidOrdersReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = tickets_factories.create_user('Alice')
        bob = tickets_factories.create_user('Bob')
        cls.order1 = tickets_factories.create_pending_order_for_self(alice, num_days=1)
        tickets_factories.create_confirmed_order_for_self(bob, num_days=2)

    def test_get_context_data(self):
        report = views.UnpaidOrdersReport()
        expected = {
            'title': 'Unpaid orders',
            'headings': ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.order1.order_id, 'individual', 'Alice', 'alice@example.com', 1, '£42', 'pending'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/unpaid-orders/')
        self.assertEqual(rsp.status_code, 200)


class TestTicketsReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = tickets_factories.create_user('Alice')
        cls.ticket1 = tickets_factories.create_ticket(alice)
        order = tickets_factories.create_confirmed_order_for_others(alice)
        cls.ticket2, cls.ticket3 = order.all_tickets()

    def test_get_context_data(self):
        report = views.TicketsReport()
        expected = {
            'title': 'All tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.ticket1.ticket_id, 'individual', 'Alice', 'Thursday, Friday, Saturday', '£90', 'Assigned'],
                [self.ticket2.ticket_id, 'individual', 'bob@example.com', 'Friday, Saturday', '£66', 'Unclaimed'],
                [self.ticket3.ticket_id, 'individual', 'carol@example.com', 'Saturday, Sunday', '£66', 'Unclaimed'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/all-tickets/')
        self.assertEqual(rsp.status_code, 200)


class TestUnclaimedTicketsReport(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = tickets_factories.create_user('Alice')
        tickets_factories.create_ticket(alice)
        order = tickets_factories.create_confirmed_order_for_others(alice)
        cls.ticket2, cls.ticket3 = order.all_tickets()

    def test_get_context_data(self):
        report = views.UnclaimedTicketsReport()
        expected = {
            'title': 'Unclaimed tickets',
            'headings': ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status'],
            'rows': [
                [self.ticket2.ticket_id, 'individual', 'bob@example.com', 'Friday, Saturday', '£66', 'Unclaimed'],
                [self.ticket3.ticket_id, 'individual', 'carol@example.com', 'Saturday, Sunday', '£66', 'Unclaimed'],
            ],
        }
        self.assertEqual(report.get_context_data(), expected)

    def test_get(self):
        rsp = self.client.get('/reports/unclaimed-tickets/')
        self.assertEqual(rsp.status_code, 200)
