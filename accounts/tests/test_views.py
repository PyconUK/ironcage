from django.test import TestCase

from tickets.tests import factories as tickets_factories

from . import factories


class ProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

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


class EditProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(year_of_birth=1985)

    def setUp(self):
        self.alice.refresh_from_db()
        self.client.force_login(self.alice)

    def test_post_update(self):
        data = {
            'year_of_birth': 1986,
            'gender': 'Female',
        }
        self.client.post('/profile/edit/', data, follow=True)
        self.alice.refresh_from_db()

        self.assertEqual(self.alice.year_of_birth, 1986)
        self.assertEqual(self.alice.gender, 'Female')
        self.assertEqual(self.alice.dont_ask_demographics, False)

    def test_post_dont_ask_again(self):
        data = {
            'dont-ask-again': '',
        }
        self.client.post('/profile/edit/', data, follow=True)
        self.alice.refresh_from_db()

        self.assertEqual(self.alice.year_of_birth, None)
        self.assertEqual(self.alice.gender, None)
        self.assertEqual(self.alice.dont_ask_demographics, True)

    def test_post_update_after_dont_ask_again(self):
        self.alice.dont_ask_demographics = True
        self.alice.save()

        data = {
            'year_of_birth': 1986,
            'gender': 'Female',
        }
        self.client.post('/profile/edit/', data, follow=True)
        self.alice.refresh_from_db()

        self.assertEqual(self.alice.year_of_birth, 1986)
        self.assertEqual(self.alice.gender, 'Female')
        self.assertEqual(self.alice.dont_ask_demographics, False)


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(password='Pa55w0rd')

    def test_get(self):
        rsp = self.client.get('/accounts/login/?next=/tickets/orders/new/')
        self.assertContains(rsp, '<input type="hidden" name="next" value="/tickets/orders/new/" />', html=True)

    def test_post_success(self):
        data = {
            'username': 'alice@example.com',
            'password': 'Pa55w0rd',
        }
        rsp = self.client.post('/accounts/login/', data, follow=True)
        self.assertContains(rsp, 'Hello, Alice')

    def test_post_failure_wrong_password(self):
        data = {
            'username': 'alice@example.com',
            'password': 'password',
        }
        rsp = self.client.post('/accounts/login/', data, follow=True)
        self.assertContains(rsp, "Your email address and password didn't match")

    def test_post_redirect(self):
        data = {
            'username': 'alice@example.com',
            'password': 'Pa55w0rd',
            'next': '/tickets/orders/new/'
        }
        rsp = self.client.post('/accounts/login/', data, follow=True)
        self.assertRedirects(rsp, '/tickets/orders/new/')


class RegisterTests(TestCase):
    def test_get(self):
        rsp = self.client.get('/accounts/register/?next=/tickets/orders/new/')
        self.assertContains(rsp, '<input type="hidden" name="next" value="/tickets/orders/new/" />', html=True)

    def test_post_success(self):
        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'password1': 'Pa55w0rd',
            'password2': 'Pa55w0rd',
        }
        rsp = self.client.post('/accounts/register/', data, follow=True)
        self.assertContains(rsp, 'Hello, Alice')

    def test_post_failure_password_mismatch(self):
        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'password1': 'Pa55w0rd',
            'password2': 'Pa55wOrd',
        }
        rsp = self.client.post('/accounts/register/', data, follow=True)
        self.assertContains(rsp, "The two password fields didn&#39;t match")

    def test_post_failure_password_too_short(self):
        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'password1': 'pw',
            'password2': 'pw',
        }
        rsp = self.client.post('/accounts/register/', data, follow=True)
        self.assertContains(rsp, 'This password is too short')

    def test_post_failure_email_taken(self):
        tickets_factories.create_user('Alice')
        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'password1': 'Pa55w0rd',
            'password2': 'Pa55w0rd',
        }
        rsp = self.client.post('/accounts/register/', data, follow=True)
        self.assertContains(rsp, 'That email address has already been registered')

    def test_post_redirect(self):
        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'password1': 'Pa55w0rd',
            'password2': 'Pa55w0rd',
            'next': '/tickets/orders/new/'
        }
        rsp = self.client.post('/accounts/register/', data, follow=True)
        self.assertRedirects(rsp, '/tickets/orders/new/')
