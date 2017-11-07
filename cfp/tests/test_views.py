from datetime import datetime, timedelta, timezone

from django_slack.utils import get_backend as get_slack_backend

from django.test import TestCase, override_settings

from cfp.models import Proposal

from . import factories


class NewProposalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/cfp/proposals/new/')
        self.assertContains(rsp, '<form method="post">')
        self.assertNotContains(rsp, 'to make a submission')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get('/cfp/proposals/new/')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/cfp/proposals/new/">sign up</a> or <a href="/accounts/login/?next=/cfp/proposals/new/">sign in</a> to make a submission.', html=True)
        self.assertNotContains(rsp, '<form method="post">')

    def test_post(self):
        self.client.force_login(self.alice)
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
        rsp = self.client.post('/cfp/proposals/new/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for submitting your proposal')

        proposal = Proposal.objects.get(title='Python is brilliant')
        self.assertEqual(proposal.proposer, self.alice)

    def test_post_sends_slack_message(self):
        backend = get_slack_backend()
        backend.reset_messages()

        self.client.force_login(self.alice)
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
        self.client.post('/cfp/proposals/new/', form_data, follow=True)

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn('Alice has just submitted a proposal for a talk (Python is brilliant: From abs to ZeroDivisionError)', text)

    def test_post_when_not_authenticated(self):
        rsp = self.client.post('/cfp/proposals/new/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class ProposalEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.proposal = factories.create_proposal(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/')
        self.assertContains(rsp, 'Update your proposal')

    def test_post(self):
        self.client.force_login(self.alice)
        form_data = {
            'session_type': 'talk',
            'title': 'Python is brilliant',
            'subtitle': 'From abs to ZeroDivisionError',
            'copresenter_names': '',
            'description': 'Let me tell you why Python is brilliant',
            'description_private': 'I am well placed to tell you why Python is brilliant',
            'aimed_at_new_programmers': True,
        }
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for updating your proposal')

        proposal = Proposal.objects.get(title='Python is brilliant')
        self.assertEqual(proposal.proposer, self.alice)
        self.assertEqual(proposal.would_like_mentor, False)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/cfp/proposals/{self.proposal.proposal_id}/edit/')

    def test_post_when_not_authenticated(self):
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/cfp/proposals/{self.proposal.proposal_id}/edit/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the proposer of a proposal can update the proposal')

    def test_post_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the proposer of a proposal can update the proposal')


class ProposalDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')

    def test_get(self):
        self.client.force_login(self.alice)
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.get(f'/cfp/proposals/{proposal.proposal_id}/delete/')
        self.assertEqual(rsp.status_code, 405)
        self.assertEqual(Proposal.objects.get(id=proposal.id), proposal)

    def test_post(self):
        self.client.force_login(self.alice)
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.post(f'/cfp/proposals/{proposal.proposal_id}/delete/', follow=True)
        self.assertContains(rsp, 'Your proposal has been withdrawn', html=True)

        with self.assertRaises(Proposal.DoesNotExist):
            Proposal.objects.get(id=proposal.id)

    def test_get_when_not_authenticated(self):
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.get(f'/cfp/proposals/{proposal.proposal_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/cfp/proposals/{proposal.proposal_id}/delete/')

    def test_post_when_not_authenticated(self):
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.post(f'/cfp/proposals/{proposal.proposal_id}/delete/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/cfp/proposals/{proposal.proposal_id}/delete/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.get(f'/cfp/proposals/{proposal.proposal_id}/delete/', follow=True)
        self.assertEqual(rsp.status_code, 405)

    def test_post_when_not_authorized(self):
        self.client.force_login(self.bob)
        proposal = factories.create_proposal(self.alice)
        rsp = self.client.post(f'/cfp/proposals/{proposal.proposal_id}/delete/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the proposer of a proposal can withdraw the proposal')


class ProposalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.proposal = factories.create_proposal(cls.alice)

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/', follow=True)
        self.assertContains(rsp, f'<a href="/cfp/proposals/{self.proposal.proposal_id}/edit/" class="btn btn-primary">Update your proposal</a>', html=True)

    def test_get_when_not_authenticated(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/')
        self.assertRedirects(rsp, f'/accounts/login/?next=/cfp/proposals/{self.proposal.proposal_id}/')

    def test_get_when_not_authorized(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the proposer of a proposal can view the proposal')


@override_settings(
    CFP_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
    CFP_DEADLINE_BYPASS_TOKEN='abc123',
)
class CFPClosedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()
        cls.proposal = factories.create_proposal(cls.alice)

    def setUp(self):
        self.client.force_login(self.alice)

    def test_get_new_proposal(self):
        rsp = self.client.get('/cfp/proposals/new/', follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, '/')

    def test_get_new_proposal_with_token(self):
        rsp = self.client.get('/cfp/proposals/new/?deadline-bypass-token=abc123')
        self.assertNotContains(rsp, 'the Call For Participation has closed')
        self.assertContains(rsp, '<form method="post">')

    def test_get_new_proposal_with_incorrect_token(self):
        rsp = self.client.get('/cfp/proposals/new/?deadline-bypass-token=321cba', follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, '/')

    @override_settings(CFP_DEADLINE_BYPASS_TOKEN=None)
    def test_get_new_proposal_when_token_not_set_in_setting(self):
        rsp = self.client.get('/cfp/proposals/new/', follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, '/')

    def test_post_new_proposal(self):
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
        rsp = self.client.post('/cfp/proposals/new/', form_data, follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, '/')

    def test_post_new_proposal_with_token(self):
        self.client.force_login(self.alice)
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
        rsp = self.client.post('/cfp/proposals/new/?deadline-bypass-token=abc123', form_data, follow=True)
        self.assertContains(rsp, 'Thank you for submitting your proposal')

    def test_get_proposal_edit_accepted(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', follow=True)
        self.assertNotContains(rsp, 'the Call For Participation has closed')
        self.assertContains(rsp, 'Update your proposal')

    def test_get_proposal_edit_rejected(self):
        self.proposal.state = 'rejected'
        self.proposal.save()

        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, f'/cfp/proposals/{self.proposal.proposal_id}/')

    def test_get_proposal_edit_with_token(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/edit/?deadline-bypass-token=abc123', follow=True)
        self.assertNotContains(rsp, 'the Call For Participation has closed')
        self.assertContains(rsp, 'Update your proposal')

    def test_post_proposal_edit_accepted(self):
        form_data = {
            'title': 'Something Different',
            'subtitle': 'Something Different',
            'copresenter_names': 'Something Different',
            'description': 'Something Different',
            'description_private': 'Something Different',
        }
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', form_data, follow=True)
        self.assertNotContains(rsp, 'Something Different')

    def test_post_proposal_edit_rejected(self):
        self.proposal.state = 'rejected'
        self.proposal.save()

        form_data = {
            'session_type': 'talk',
            'title': 'Python is brilliant',
            'subtitle': 'From abs to ZeroDivisionError',
            'copresenter_names': '',
            'description': 'Let me tell you why Python is brilliant',
            'description_private': 'I am well placed to tell you why Python is brilliant',
            'aimed_at_new_programmers': True,
        }
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', form_data, follow=True)
        self.assertContains(rsp, 'the Call For Participation has closed')
        self.assertRedirects(rsp, f'/cfp/proposals/{self.proposal.proposal_id}/')

    def test_post_proposal_edit_with_token(self):
        form_data = {
            'session_type': 'talk',
            'title': 'Python is brilliant',
            'subtitle': 'From abs to ZeroDivisionError',
            'copresenter_names': '',
            'description': 'Let me tell you why Python is brilliant',
            'description_private': 'I am well placed to tell you why Python is brilliant',
            'aimed_at_new_programmers': True,
        }
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/?deadline-bypass-token=abc123', form_data, follow=True)
        self.assertNotContains(rsp, 'the Call For Participation has closed')
        self.assertContains(rsp, 'Thank you for updating your proposal')

    def test_post_proposal_update_accepted(self):
        form_data = {
            'slides_url': 'https://slidedeck.com/mytalk',
            'info_url': 'https://github.com/mycode',
            'video_url': 'https://youtube.com/myvideo',
            'transcription': 'Hello everyone. Python is brilliant. Thanks for listening.',
        }
        rsp = self.client.post(f'/cfp/proposals/{self.proposal.proposal_id}/edit/', form_data, follow=True)
        self.assertNotContains(rsp, 'the Call For Participation has closed')
        self.assertContains(rsp, 'Thank you for updating your proposal')

    def test_get_proposal_accepted(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/', follow=True)
        self.assertContains(rsp, 'Update your proposal')

    def test_get_proposal_not_accepted(self):
        self.proposal.state = 'rejected'
        self.proposal.save()

        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/', follow=True)
        self.assertNotContains(rsp, 'Update your proposal')

    def test_get_proposal_with_token(self):
        rsp = self.client.get(f'/cfp/proposals/{self.proposal.proposal_id}/?deadline-bypass-token=abc123')
        self.assertContains(rsp, 'Update your proposal')
