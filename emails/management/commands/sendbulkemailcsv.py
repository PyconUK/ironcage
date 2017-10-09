import csv
import re

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template

from ironcage.emails import send_mail


class Command(BaseCommand):
    help = '''
Sends emails to everybody listed in a CSV file.

As opposed to sendbulkemail, this command is designed to be run locally and not
on heroku.  As such, you will need to have set the MAILGUN_* environment
variables.

The CSV file should have headers, and one column, "email_addr" is mandatory.
Other colunms may contain values which will be passed to the template for
rendering each eamil.

For instance,

$ ./manage.py sendbulkemailcsv --recipients people.csv --template csv-test \\
        --subject 'This is a test'

will send an email to everybody listed in people.csv.  The email will be
constructed from the template at emails/templates/emails/csv-test.txt, and
will have subject "This is a test".
    '''.strip()

    def add_arguments(self, parser):
        parser.add_argument('--template', required=True, help='Base name of template file')
        parser.add_argument('--subject', required=True, help='Subject of email')
        parser.add_argument('--recipients', required=True, help='Path to CSV file of recipients')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, template, subject, recipients, dry_run, **kwargs):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

        template = get_template(f'emails/{template}.txt')

        with open(recipients) as f:
            recipients = list(csv.DictReader(f))

        num_recipients = len(recipients)

        if dry_run:
            self.stdout.write('This is a dry run')
            self.stdout.write(f'Running this would send the email to {num_recipients} recipient(s)')
        else:
            self.stdout.write(f'About to send the email to {num_recipients} recipient(s)')

        for recipient in recipients:
            # Here, we are making sure that template.render() raises no errors,
            # *before* we start to send any emails.
            body = render(template, recipient)
            assert 'THIS SHOULD NEVER HAPPEN' not in body, f'Could not render template for {recipient["email_addr"]}'
            if dry_run:
                self.stdout.write(body)

        if dry_run:
            return

        self.stdout.write('Are you sure? [yN]')

        while True:
            rsp = input()
            if rsp in ['', 'n', 'N']:
                self.stdout.write('Aborting')
                return
            elif rsp in ['y', 'Y']:
                break

        self.stdout.write(f'Sending {num_recipients} email(s)')

        for recipient in recipients:
            body = render(template, recipient)
            qualified_subject = subject
            send_mail(
                qualified_subject,
                body,
                recipient['email_addr'],
            )


def render(template, context):
    body = template.render(context)
    body = '\n'.join(line.lstrip() for line in body.splitlines())
    body = re.sub(r'\n\n+', '\n\n', body)
    body = body.replace('&#39;', "'")
    body = body.replace('&amp;', '&')
    return body
