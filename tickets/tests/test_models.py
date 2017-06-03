from django.test import TestCase

from . import factories


class OrderTests(TestCase):
    def test_cost_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(order.cost(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_cost_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        self.assertEqual(order.cost(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_ticket_details_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        ticket_ids = [t.ticket_id for t in order.all_tickets()]
        expected_details = [{
            'id': ticket_ids[0],
            'name': 'Alice',
            'days': 'Thursday, Friday, Saturday',
            'cost': 90,
        }, {
            'id': ticket_ids[1],
            'name': 'bob@example.com',
            'days': 'Friday, Saturday',
            'cost': 66,
        }, {
            'id': ticket_ids[2],
            'name': 'carol@example.com',
            'days': 'Saturday, Sunday',
            'cost': 66,
        }]
        self.assertEqual(order.ticket_details(), expected_details)

    def test_ticket_details_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        expected_details = [{
            'name': 'Alice',
            'days': 'Thursday, Friday, Saturday',
            'cost': 90,
        }, {
            'name': 'bob@example.com',
            'days': 'Friday, Saturday',
            'cost': 66,
        }, {
            'name': 'carol@example.com',
            'days': 'Saturday, Sunday',
            'cost': 66,
        }]
        self.assertEqual(order.ticket_details(), expected_details)
