from django_slack.utils import get_backend as get_slack_backend
from django.test import TestCase
from . import factories
from ukpa.models import Nomination


class NewNominationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/ukpa/nominations/new/')
        self.assertContains(rsp, '<form method="post">')
        self.assertNotContains(rsp, 'to make a nominaton')

    def test_get_when_user_has_nomination(self):
        nomination = factories.create_nomination(self.alice)
        self.client.force_login(self.alice)
        rsp = self.client.get('/ukpa/nominations/new/', follow=True)
        self.assertRedirects(rsp, f'/ukpa/nominations/{nomination.nomination_id}/')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get('/ukpa/nominations/new/')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/ukpa/nominations/new/">sign up</a> or <a href="/accounts/login/?next=/ukpa/nominations/new/">sign in</a> to make a nomination.', html=True)
        self.assertNotContains(rsp, '<form method="post">')

    def test_post(self):
        self.client.force_login(self.alice)
        test_statement = 'Hello. I would like to be a UKPA Trustee.'
        form_data = {
            'statement': test_statement,
        }
        rsp = self.client.post('/ukpa/nominations/new/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for submitting your nomination')

        nomination = self.alice.get_nomination()
        self.assertEqual(nomination.statement, test_statement)

    def test_post_sends_slack_message(self):
        backend = get_slack_backend()
        backend.reset_messages()

        self.client.force_login(self.alice)
        test_statement = 'Hello. I would like to be a UKPA Trustee.'
        form_data = {
            'statement': test_statement,
        }
        self.client.post('/ukpa/nominations/new/', form_data, follow=True)

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('New nomination', text)

    def test_post_when_user_has_nomination(self):
        nomination = factories.create_nomination(self.alice)
        self.client.force_login(self.alice)
        rsp = self.client.post('/ukpa/nominations/new/', follow=True)
        self.assertRedirects(rsp, f'/ukpa/nominations/{nomination.nomination_id}/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post('/ukpa/nominations/new/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class NominationEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.nomination = factories.create_nomination(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/')
        self.assertContains(rsp, 'Update your nomination')

    def test_post(self):
        self.client.force_login(self.alice)
        test_statement = 'Hello. I would still like to be a UKPA Trustee.'
        form_data = {
            'statement': test_statement,
        }
        rsp = self.client.post(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for updating your nomination')

        nomination = self.alice.get_nomination()
        nomination.refresh_from_db()
        self.assertEqual(nomination.statement, test_statement)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/ukpa/nominations/{self.nomination.nomination_id}/edit/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/ukpa/nominations/{self.nomination.nomination_id}/edit/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the nominee can update the nomination')

    def test_post_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the nominee can update the nomination')


class NominationDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')

    def test_get(self):
        self.client.force_login(self.alice)
        nomination = factories.create_nomination(self.alice)
        rsp = self.client.get(f'/ukpa/nominations/{nomination.nomination_id}/delete/')
        self.assertRedirects(rsp, '/')
        self.assertEqual(Nomination.objects.get(id=nomination.id), nomination)

    def test_post(self):
        self.client.force_login(self.alice)
        nomination = factories.create_nomination(self.alice)
        rsp = self.client.post(f'/ukpa/nominations/{nomination.nomination_id}/delete/', follow=True)
        self.assertContains(rsp, 'Your nomination has been withdrawn', html=True)

        with self.assertRaises(Nomination.DoesNotExist):
            Nomination.objects.get(id=nomination.id)

    def test_get_when_not_authenticated(self):
        nomination = factories.create_nomination(self.alice)
        rsp = self.client.get(f'/ukpa/nominations/{nomination.nomination_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/ukpa/nominations/{nomination.nomination_id}/delete/')

    def test_post_when_not_authenticated(self):
        nomination = factories.create_nomination(self.alice)
        rsp = self.client.post(f'/ukpa/nominations/{nomination.nomination_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/ukpa/nominations/{nomination.nomination_id}/delete/')

    def test_get_when_not_authorized(self):
        nomination = factories.create_nomination(self.alice)
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/ukpa/nominations/{nomination.nomination_id}/delete/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the nominee can withdraw the nomination')

    def test_post_when_not_authorized(self):
        nomination = factories.create_nomination(self.alice)
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/ukpa/nominations/{nomination.nomination_id}/delete/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the nominee can withdraw the nomination')


class NominationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.nomination = factories.create_nomination(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/', follow=True)
        self.assertContains(rsp, f'<a href="/ukpa/nominations/{self.nomination.nomination_id}/delete/" class="btn btn-danger">Withdraw your nomination</a>', html=True)
        self.assertContains(rsp, f'<a href="/ukpa/nominations/{self.nomination.nomination_id}/edit/" class="btn btn-primary">Update your nomination</a>', html=True)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/ukpa/nominations/{self.nomination.nomination_id}/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/ukpa/nominations/{self.nomination.nomination_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the nominee can view the nomination')
