from django.core.management import BaseCommand
from django.db.models import Q

from ...actions import create_free_ticket

from accounts.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, dry_run, **kwargs):
        for u in User.objects.filter(
            Q(grant_application__amount_offered__gt=0) | Q(grant_application__requested_ticket_only=True),
            ticket=None
        ):
            print(u.email_addr)
            if not dry_run:
                create_free_ticket(u.email_addr, 'Financial assistance')
