import re

from django.core.management import BaseCommand
from django.template.loader import get_template

from ironcage.emails import send_mail
from tickets.models import TicketInvitation

import structlog
logger = structlog.get_logger()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--template', required=True, help='Base name of template file')
        parser.add_argument('--subject', required=True, help='Subject of email')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, template, subject, dry_run, **kwargs):
        template = get_template(f'emails/{template}.txt')

        invitations = TicketInvitation.objects.filter(status='unclaimed')
        num_recipients = len(invitations)

        for invitation in invitations:
            # Here, we are making sure that template.render() raises no errors,
            # *before* we start to send any emails.
            context = {'invitation': invitation}
            body = render(template, context)
            assert 'THIS SHOULD NEVER HAPPEN' not in body, f'Could not render template'

        if dry_run:
            self.stdout.write('This is a dry run')
            self.stdout.write(f'Running this would send the email to {num_recipients} recipient(s)')
            self.stdout.write(body)
            return

        self.stdout.write(f'Sending {num_recipients} email(s)')
        self.stdout.write('Are you sure? [yN]')

        while True:
            rsp = input()
            if rsp in ['', 'n', 'N']:
                self.stdout.write('Aborting')
                return
            elif rsp in ['y', 'Y']:
                break

        logger.info('sending ticket reminder', template=template.template.name, num_recipients=num_recipients)

        for invitation in invitations:
            context = {'invitation': invitation}
            body = render(template, context)
            qualified_subject = f'{subject} | {invitation.ticket.ticket_id}'
            logger.info('sending email', email_addr=invitation.email_addr)
            send_mail(
                qualified_subject,
                body,
                invitation.email_addr,
            )


def render(template, context):
    body = template.render(context)
    body = '\n'.join(line.lstrip() for line in body.splitlines())
    body = re.sub(r'\n\n+', '\n\n', body)
    body = body.replace('&#39;', "'")
    body = body.replace('&amp;', '&')
    return body
