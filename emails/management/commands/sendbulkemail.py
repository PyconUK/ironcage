from argparse import RawTextHelpFormatter
import os
import re

from django.core.management import BaseCommand
from django.template.loader import get_template

from accounts.models import User
from ironcage.emails import send_mail

import structlog
logger = structlog.get_logger()


class Command(BaseCommand):
    help = '''
Sends emails to all users belonging to a given pre-defined queryset.

For instance,

$ ./manage.py sendbulkemail --recipients staff --template staff-test \\
        --subject 'This is a test'

will send an email to all staff users.  The email will be constructed from
the template at emails/templates/emails/staff-test.txt, and will have
subject "This is a test".
    '''.strip()

    recipients = {
        'admins': User.objects.filter(email_addr__in=os.environ.get('ADMINS', '').split(',')),
        'staff': User.objects.filter(is_staff=True),
        'all': User.objects.all(),
        'ticket-holders': User.objects.exclude(ticket=None),
        'cfp-proposers': User.objects.filter(
            proposals__isnull=False,
            proposals__special_reply_required=False,
        ).distinct(),
        'grant-applicants-without-cfp-proposal': User.objects.filter(
            grant_application__isnull=False,
            grant_application__special_reply_required=False,
            proposals__isnull=True,
        ).distinct(),
    }

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument('--template', required=True, help='Base name of template file')
        parser.add_argument('--subject', required=True, help='Subject of email')
        parser.add_argument('--recipients', required=True, choices=self.recipients, help='Recipients of email')
        parser.add_argument('--list-recipients', action='store_true', help='If provided, lists recipients before sending')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, template, subject, recipients, list_recipients, dry_run, **kwargs):
        template = get_template(f'emails/{template}.txt')

        recipients = self.recipients[recipients]
        num_recipients = recipients.count()

        if dry_run:
            self.stdout.write('This is a dry run')
            self.stdout.write(f'Running this would send the email to {num_recipients} recipient(s)')
        else:
            self.stdout.write(f'About to send the email to {num_recipients} recipient(s)')

        for recipient in recipients.order_by('email_addr'):
            if list_recipients:
                if dry_run:
                    self.stdout.write('~' * 80)
                self.stdout.write(f' * {recipient.name} ({recipient.email_addr})')

            # Here, we are making sure that template.render() raises no errors,
            # *before* we start to send any emails.
            context = {'recipient': recipient}
            body = render(template, context)
            assert 'THIS SHOULD NEVER HAPPEN' not in body, f'Could not render template for {recipient.email_addr}'
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
        logger.info('sending bulk email', template=template.template.name, num_recipients=num_recipients)

        for recipient in recipients.order_by('id'):
            context = {'recipient': recipient}
            body = render(template, context)
            qualified_subject = f'[{recipient.user_id}] {subject}'
            logger.info('sending email', recipient=recipient.id, email_addr=recipient.email_addr)
            send_mail(
                qualified_subject,
                body,
                recipient.email_addr,
            )


def render(template, context):
    body = template.render(context)
    body = '\n'.join(line.lstrip() for line in body.splitlines())
    body = re.sub(r'\n\n+', '\n\n', body)
    body = body.replace('&#39;', "'")
    body = body.replace('&amp;', '&')
    return body
