import csv
import sys

from django.core.management import BaseCommand

from tickets.models import Ticket


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        writer = csv.writer(sys.stdout)

        for ticket in Ticket.objects.all():
            user = ticket.owner
            if user is None:
                name = None
                email_addr = ticket.invitation.email_addr
                is_staff = False
                is_contributor = False
            else:
                name = user.name
                email_addr = user.email_addr
                is_staff = user.is_staff
                is_contributor = user.is_contributor

            if ticket.pot is None:
                company_name = ticket.order.company_name
            elif 'Sponsor: ' in ticket.pot:
                company_name = ticket.pot[len('Sponsor: '):]
            else:
                company_name = None

            if user is not None and user.is_staff:
                company_name = 'PyCon UK committee'

            days = ', '.join(day.title() for day in ticket.days_abbrev())

            writer.writerow([ticket.ticket_id, name, email_addr, company_name, days, is_staff, is_contributor])
