from django.test import TestCase

from accounts.tests import factories as accounts_factories


class NavTests(TestCase):
    def test_user_authenticated(self):
        user = accounts_factories.create_user()
        self.client.force_login(user)

        rsp = self.client.get('/tickets/orders/new/')
        self.assertContains(rsp, '<a href="/accounts/logout/">Sign out</a>', html=True)
        self.assertNotContains(rsp, 'Sign in')
        self.assertNotContains(rsp, 'Sign up')

    def test_user_not_authenticated(self):
        rsp = self.client.get('/tickets/orders/new/')
        self.assertContains(rsp, '<a href="/accounts/login/?next=/tickets/orders/new/">Sign in</a>', html=True)
        self.assertContains(rsp, '<a href="/accounts/register/?next=/tickets/orders/new/">Sign up</a>', html=True)
        self.assertNotContains(rsp, 'Sign out')
