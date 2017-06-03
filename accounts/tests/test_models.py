from django.test import TestCase

from tickets.tests import factories as tickets_factories

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
            password='secret',
        )

        tickets_factories.create_ticket(user)

        self.assertIsNotNone(user.ticket())

    def test_ticket_when_none(self):
        user = User.objects.create_user(
            email_addr='alice@example.com',
            name='Alice',
            password='secret',
        )

        self.assertIsNone(user.ticket())
