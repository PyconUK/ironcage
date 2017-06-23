from django.test import TestCase

from . import factories


class ProfileTests(TestCase):
    def test_get_profile_when_not_authenticated(self):
        rsp = self.client.get('/profile/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/?next=/profile/')

    def test_get_profile_for_user_with_empty_profile(self):
        self.client.force_login(factories.create_user())
        rsp = self.client.get('/profile/')
        for k, v in [
            ['Name', 'Alice'],
            ['Email', 'alice@example.com'],
            ['Accessibility', 'unknown'],
            ['Childcare', 'unknown'],
            ['Dietary', 'unknown'],
            ['Year of birth', 'unknown'],
            ['Gender', 'unknown'],
            ['Ethnicity', 'unknown'],
            ['Nationality', 'unknown'],
            ['Country of residence', 'unknown'],
        ]:
            self.assertContains(rsp, f'<tr><th class="col-md-4">{k}</th><td>{v}</td></tr>', html=True)
        self.assertNotContains(rsp, 'You have opted not to share demographic information with us')

    def test_get_profile_for_user_with_full_profile(self):
        self.client.force_login(factories.create_user_with_full_profile())
        rsp = self.client.get('/profile/')
        for k, v in [
            ['Name', 'Alice'],
            ['Email', 'alice@example.com'],
            ['Accessibility', 'none'],
            ['Childcare', 'none'],
            ['Dietary', 'Vegan'],
            ['Year of birth', '1985'],
            ['Gender', 'Female'],
            ['Ethnicity', 'Mixed'],
            ['Nationality', 'British'],
            ['Country of residence', 'United Kingdom'],
        ]:
            self.assertContains(rsp, f'<tr><th class="col-md-4">{k}</th><td>{v}</td></tr>', html=True)
        self.assertNotContains(rsp, 'You have opted not to share demographic information with us')

    def test_get_profile_for_user_with_dont_ask_demographics_set(self):
        self.client.force_login(factories.create_user_with_dont_ask_demographics_set())
        rsp = self.client.get('/profile/')
        self.assertContains(rsp, 'You have opted not to share demographic information with us')


class EditProfileTests(TestCase):
    def test_post_update(self):
        alice = factories.create_user(year_of_birth=1985)
        self.client.force_login(alice)

        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'year_of_birth': 1986,
            'gender': 'Female',
        }
        self.client.post('/profile/edit/', data, follow=True)
        alice.refresh_from_db()

        self.assertEqual(alice.year_of_birth, 1986)
        self.assertEqual(alice.gender, 'Female')
        self.assertEqual(alice.dont_ask_demographics, False)

    def test_post_dont_ask_demographics(self):
        alice = factories.create_user(year_of_birth=1985)
        self.client.force_login(alice)

        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'dont_ask_demographics': 'on',
            'year_of_birth': 1986,
            'gender': 'Female',
        }
        self.client.post('/profile/edit/', data, follow=True)
        alice.refresh_from_db()

        self.assertEqual(alice.year_of_birth, None)
        self.assertEqual(alice.gender, None)
        self.assertEqual(alice.dont_ask_demographics, True)

    def test_post_update_after_dont_ask_again(self):
        alice = factories.create_user_with_dont_ask_demographics_set(year_of_birth=1985)
        self.client.force_login(alice)

        data = {
            'name': 'Alice',
            'email_addr': 'alice@example.com',
            'year_of_birth': 1986,
            'gender': 'Female',
        }
        self.client.post('/profile/edit/', data, follow=True)
        alice.refresh_from_db()

        self.assertEqual(alice.year_of_birth, 1986)
        self.assertEqual(alice.gender, 'Female')
        self.assertEqual(alice.dont_ask_demographics, False)


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
        factories.create_user()
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
