import contextlib
from unittest.mock import patch

from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase


class ErrorReportingTests(TestCase):
    @patch('logging.StreamHandler.emit')
    def test_writes_to_console(self, mock_emit):
        with contextlib.suppress(ZeroDivisionError):
            self.client.get('/500/')
        self.assertIn('Internal Server Error', mock_emit.call_args[0][0].msg)

    # We patch emit so that we don't spam stderr when running the test
    @patch('logging.StreamHandler.emit')
    def test_sends_to_slack(self, mock_emit):
        backend = get_slack_backend()
        backend.reset_messages()

        with contextlib.suppress(ZeroDivisionError):
            self.client.get('/500/')

        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['text'], 'ERROR (EXTERNAL IP): Internal Server Error: /500/')

    # We patch emit so that we don't spam stderr when running the test
    @patch('logging.StreamHandler.emit')
    def test_emails_admins(self, mock_emit):
        with contextlib.suppress(ZeroDivisionError):
            self.client.get('/500/')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, '[Django] ERROR (EXTERNAL IP): Internal Server Error: /500/')
