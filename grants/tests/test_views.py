from datetime import datetime, timedelta, timezone

from django_slack.utils import get_backend as get_slack_backend

from django.test import TestCase, override_settings
from grants.models import Application
from . import factories


class NewApplicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/grants/applications/new/')
        self.assertContains(rsp, '<form method="post">')
        self.assertNotContains(rsp, 'to make an application')

    def test_get_when_user_has_application(self):
        application = factories.create_application(self.alice)
        self.client.force_login(self.alice)
        rsp = self.client.get('/grants/applications/new/', follow=True)
        self.assertRedirects(rsp, f'/grants/applications/{application.application_id}/')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get('/grants/applications/new/')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/grants/applications/new/">sign up</a> or <a href="/accounts/login/?next=/grants/applications/new/">sign in</a> to make an application.', html=True)
        self.assertNotContains(rsp, '<form method="post">')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'amount_requested': '1000',
            'days': ['sat', 'sun', 'mon'],
            'about_you': 'I have two thumbs',
        }
        rsp = self.client.post('/grants/applications/new/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for submitting your application')

        application = self.alice.get_grant_application()
        self.assertEqual(application.amount_requested, 1000)
        self.assertEqual(application.days(), ['Saturday', 'Sunday', 'Monday'])

    def test_post_sends_slack_message(self):
        backend = get_slack_backend()
        backend.reset_messages()

        self.client.force_login(self.alice)
        form_data = {
            'amount_requested': '1000',
            'days': ['sat', 'sun', 'mon'],
            'about_you': 'I have two thumbs',
        }
        self.client.post('/grants/applications/new/', form_data, follow=True)

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('New grant application', text)

    def test_post_when_user_has_application(self):
        application = factories.create_application(self.alice)
        self.client.force_login(self.alice)
        rsp = self.client.post('/grants/applications/new/', follow=True)
        self.assertRedirects(rsp, f'/grants/applications/{application.application_id}/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post('/grants/applications/new/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class ApplicationEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.application = factories.create_application(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/edit/')
        self.assertContains(rsp, 'Update your application')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'amount_requested': '2000',
            'days': ['fri', 'sat', 'sun', 'mon'],
            'about_you': 'I have two thumbs',
        }
        rsp = self.client.post(f'/grants/applications/{self.application.application_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for updating your application')

        application = self.alice.get_grant_application()
        application.refresh_from_db()
        self.assertEqual(application.amount_requested, 2000)
        self.assertEqual(application.days(), ['Friday', 'Saturday', 'Sunday', 'Monday'])

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/grants/applications/{self.application.application_id}/edit/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(f'/grants/applications/{self.application.application_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/grants/applications/{self.application.application_id}/edit/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a application can update the application')

    def test_post_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.post(f'/grants/applications/{self.application.application_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a application can update the application')


class ApplicationDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')

    def test_get(self):
        self.client.force_login(self.alice)
        application = factories.create_application(self.alice)
        rsp = self.client.get(f'/grants/applications/{application.application_id}/delete/')
        self.assertEqual(rsp.status_code, 405)
        self.assertEqual(Application.objects.get(id=application.id), application)

    def test_post(self):
        self.client.force_login(self.alice)
        application = factories.create_application(self.alice)
        rsp = self.client.post(f'/grants/applications/{application.application_id}/delete/', follow=True)
        self.assertContains(rsp, 'Your application has been withdrawn', html=True)

        with self.assertRaises(Application.DoesNotExist):
            Application.objects.get(id=application.id)

    def test_get_when_not_authenticated(self):
        application = factories.create_application(self.alice)
        rsp = self.client.get(f'/grants/applications/{application.application_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/grants/applications/{application.application_id}/delete/')

    def test_post_when_not_authenticated(self):
        application = factories.create_application(self.alice)
        rsp = self.client.post(f'/grants/applications/{application.application_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/grants/applications/{application.application_id}/delete/')


class ApplicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.application = factories.create_application(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/', follow=True)
        self.assertContains(rsp, f'<a href="/grants/applications/{self.application.application_id}/edit/" class="btn btn-primary">Update your application</a>', html=True)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/grants/applications/{self.application.application_id}/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a application can view the application')


@override_settings(GRANT_APPLICATIONS_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
class ApplicationsClosedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.application = factories.create_application(cls.alice)

    def setUp(self):
        self.client.force_login(self.alice)

    def test_get_new_application(self):
        rsp = self.client.get('/grants/applications/new/', follow=True)
        self.assertContains(rsp, 'financial assistance applications are closed')
        self.assertRedirects(rsp, '/')

    def test_post_new_application(self):
        form_data = {
            'session_type': 'talk',
            'title': 'Python is brilliant',
            'subtitle': 'From abs to ZeroDivisionError',
            'copresenter_names': '',
            'description': 'Let me tell you why Python is brilliant',
            'description_private': 'I am well placed to tell you why Python is brilliant',
            'aimed_at_new_programmers': True,
            'would_like_mentor': True,
        }
        rsp = self.client.post('/grants/applications/new/', form_data, follow=True)
        self.assertContains(rsp, 'financial assistance applications are closed')
        self.assertRedirects(rsp, '/')

    def test_get_application_edit(self):
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/edit/', follow=True)
        self.assertContains(rsp, 'financial assistance applications are closed')
        self.assertRedirects(rsp, f'/grants/applications/{self.application.application_id}/')

    def test_post_application_edit(self):
        form_data = {
            'session_type': 'talk',
            'title': 'Python is brilliant',
            'subtitle': 'From abs to ZeroDivisionError',
            'copresenter_names': '',
            'description': 'Let me tell you why Python is brilliant',
            'description_private': 'I am well placed to tell you why Python is brilliant',
            'aimed_at_new_programmers': True,
        }
        rsp = self.client.post(f'/grants/applications/{self.application.application_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, 'financial assistance applications are closed')
        self.assertRedirects(rsp, f'/grants/applications/{self.application.application_id}/')

    def test_get_application(self):
        rsp = self.client.get(f'/grants/applications/{self.application.application_id}/', follow=True)
        self.assertNotContains(rsp, 'Update your application')
