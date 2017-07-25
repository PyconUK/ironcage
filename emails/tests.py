from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdin
from django.utils.six import StringIO

from accounts.tests import factories as accounts_factories


class SendBulkEmailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        accounts_factories.create_staff_user(name='Alice', email_addr='alice@example.com')
        accounts_factories.create_staff_user(name='Bob', email_addr='bob@example.com')
        accounts_factories.create_user(name='Carol')

    def test_dry_run(self):
        stdout = StringIO()
        call_command(
            'sendbulkemail',
            '--recipients=staff',
            '--template=staff-test',
            '--subject="This is a test"',
            '--dry-run',
            stdout=stdout,
        )

        self.assertIn('This is a dry run', stdout.getvalue())
        self.assertIn('Running this would send the email to 2 recipient(s)', stdout.getvalue())

    def test_wet_run(self):
        stdout = StringIO()
        with captured_stdin() as stdin:
            stdin.write('Y\n')
            stdin.seek(0)

            call_command(
                'sendbulkemail',
                '--recipients=staff',
                '--template=staff-test',
                '--subject=This is a test',
                stdout=stdout,
            )

        self.assertIn('About to send the email to 2 recipient(s)', stdout.getvalue())
        self.assertIn('Sending 2 email(s)', stdout.getvalue())

        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2017 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, 'This is a test')
        self.assertIn('Hi Alice', email.body)
