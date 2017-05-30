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

    def test_cost(self):
        self.assertEqual(self.order.cost(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_ticket_details(self):
        expected_details = [{
            'id': '9A19',
            'name': 'Alice',
            'days': 'Thursday, Friday, Saturday',
            'cost': 90,
        }, {
            'id': '2C62',
            'name': 'bob@example.com',
            'days': 'Friday, Saturday',
            'cost': 66,
        }, {
            'id': 'BEAB',
            'name': 'carol@example.com',
            'days': 'Saturday, Sunday',
            'cost': 66,
        }]
        self.assertEqual(self.order.ticket_details(), expected_details)
