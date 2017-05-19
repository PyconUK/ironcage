from django.db import models
from django.urls import reverse

from django.contrib.auth.models import User

from .constants import DAYS, RATES


class Order(models.Model):
    purchaser = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    rate = models.CharField(max_length=40)

    class Manager(models.Manager):
        # TODO where do transactions go?
        def create_with_ticket_for_purchaser(self, purchaser, rate, days):
            order = self.create(purchaser=purchaser, rate=rate)
            order.tickets.create_for_user(purchaser, days)
            return order

        def create_with_tickets_for_others(self, purchaser, rate, email_addrs_and_days):
            order = self.create(purchaser=purchaser, rate=rate)
            for email_addr, days in email_addrs_and_days:
                order.tickets.create_with_invitation(email_addr, days)
            return order

        def create_with_tickets_for_purchaser_and_others(self, purchaser, rate, purchaser_days, email_addrs_and_days):
            order = self.create(purchaser=purchaser, rate=rate)
            order.tickets.create_for_user(purchaser, purchaser_days)
            for email_addr, days in email_addrs_and_days:
                order.tickets.create_with_invitation(email_addr, days)
            return order

    objects = Manager()

    def get_absolute_url(self):
        return reverse('tickets:order', args=[self.id])

    def ticket_details(self):
        return [ticket.details() for ticket in self.tickets.all()]

    def cost(self):
        return sum(ticket.cost() for ticket in self.tickets.all())

    def num_tickets(self):
        return self.tickets.count()

    def unclaimed_tickets(self):
        return self.tickets.filter(owner=None)


class Ticket(models.Model):
    order = models.ForeignKey(Order, related_name='tickets', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='tickets', null=True, on_delete=models.CASCADE)
    thu = models.BooleanField()
    fri = models.BooleanField()
    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()

    class Manager(models.Manager):
        def create_for_user(self, user, days):
            day_fields = {day: (day in days) for day in DAYS}
            self.create(owner=user, **day_fields)

        def create_with_invitation(self, email_addr, days):
            day_fields = {day: (day in days) for day in DAYS}
            ticket = self.create(**day_fields)
            ticket.invitations.create(email_addr=email_addr)

    objects = Manager()

    def details(self):
        return {
            'id': self.id,
            'name': self.ticket_holder_name(),
            'days': ', '.join(self.days()),
            'cost': self.cost(),
        }

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]

    def ticket_holder_name(self):
        if self.owner:
            return self.owner.username  # TODO use name in profile if available
        else:
            return self.invitation().email_addr

    def cost(self):
        rate = self.order.rate
        return RATES[rate]['ticket_price'] + RATES[rate]['day_price'] * len(self.days())

    def invitation(self):
        # This will raise an exception if a ticket has multiple invitations
        return self.invitations.get()


class TicketInvitation(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='invitations', on_delete=models.CASCADE)
    email_addr = models.EmailField()
