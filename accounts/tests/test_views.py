from django.test import TestCase

from tickets.tests import factories as tickets_factories

from accounts.models import User


class ProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(email_addr='alice@example.com', name='Alice')

    def setUp(self):
        self.client.force_login(self.alice)

    def test_get_profile_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/profile/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/profile/')

    def test_get_profile_with_no_ticket(self):
        rsp = self.client.get('/profile/')
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Buy one now!</a>', html=True)

    def test_get_profile_with_ticket(self):
        tickets_factories.create_ticket(self.alice)

        rsp = self.client.get('/profile/')
        self.assertNotContains(rsp, '<a href="/tickets/orders/new/">Buy one now!</a>', html=True)
        self.assertContains(rsp, 'You have a ticket for Thursday, Friday, Saturday')