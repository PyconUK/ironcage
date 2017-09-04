from django.core.management import BaseCommand

from ...actions import create_free_ticket


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--pot', required=True, help='Pot to which tickets are to be assigned')

    def handle(self, *args, pot, **kwargs):
        self.stdout.write('Enter email addresses to send ticket invitations to')
        while True:
            email_addr = input().strip()
            try:
                if email_addr == '':
                    break
                create_free_ticket(email_addr, pot)
            except (KeyboardInterrupt, EOFError):
                break
