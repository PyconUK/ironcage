from django.test import TestCase

from tickets import actions as ticket_actions

from accounts.models import User


class UserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email_addr='alice@example.com',
            name='Alice',
            password='secret',
        )

        self.assertEqual(user.email_addr, 'alice@example.com')
        self.assertTrue(user.check_password('secret'))
        self.assertEqual(user.name, 'Alice')

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email_addr='alice@example.com',
            name='Alice',
            password='secret',
        )

        self.assertEqual(user.email_addr, 'alice@example.com')
        self.assertTrue(user.check_password('secret'))
        self.assertEqual(user.name, 'Alice')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_ticket(self):
        user = User.objects.create_user(
            email_addr='alice@example.com',
            name='Alice',
        )

        self.assertIsNone(user.ticket())

        ticket_actions.place_order_for_self(
            user,
            'individual',
            ['thu', 'fri', 'sat'],
        )

        self.assertIsNotNone(user.ticket())
