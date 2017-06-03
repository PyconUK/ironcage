from django.test import TestCase

from accounts.models import User

from tickets import actions


class OrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')
        cls.order = actions.place_order_for_self_and_others(
            alice,
            'individual',
            ['thu', 'fri', 'sat'],
            [
                ('bob@example.com', ['fri', 'sat']),
                ('carol@example.com', ['sat', 'sun']),
            ]
        )

    def setUp(self):
        self.order.refresh_from_db()

    def test_cost_for_confirmed_order(self):
        actions.confirm_order(self.order, 'ch_abcdefghijklmnopqurstuvw')
        self.assertEqual(self.order.cost(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_cost_for_unconfirmed_order(self):
        self.assertEqual(self.order.cost(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_ticket_details_for_confirmed_order(self):
        actions.confirm_order(self.order, 'ch_abcdefghijklmnopqurstuvw')
        ticket_ids = [t.ticket_id for t in self.order.all_tickets()]
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
        self.assertEqual(self.order.ticket_details(), expected_details)

    def test_ticket_details_for_unconfirmed_order(self):
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
        self.assertEqual(self.order.ticket_details(), expected_details)
