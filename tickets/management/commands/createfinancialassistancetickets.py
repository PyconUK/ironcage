from django.core.management import BaseCommand
from django.db.models import Q

from ...actions import create_free_ticket

from accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for u in User.objects.filter(
            Q(grant_application__amount_offered__gt=0) | Q(requested_ticket_only=True),
            ticket=None
        ):
            create_free_ticket(u.email_addr, 'Financial assistance')
