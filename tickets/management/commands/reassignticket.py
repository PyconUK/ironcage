from django.core.management import BaseCommand

from ...actions import reassign_ticket
from ...models import Ticket


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ticket_id')
        parser.add_argument('email_addr')

    def handle(self, *args, ticket_id, email_addr, **kwargs):
        ticket = Ticket.objects.get_by_order_id_or_404(ticket_id)
        reassign_ticket(ticket, email_addr)
