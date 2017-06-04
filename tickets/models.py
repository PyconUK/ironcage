from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

from .constants import DAYS, RATES
from .utils import Scrambler


class Order(models.Model):
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    rate = models.CharField(max_length=40)
    status = models.CharField(max_length=10)
    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_failure_reason = models.CharField(max_length=400, blank=True)
    unconfirmed_details = JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(1000)

    class Manager(models.Manager):
        def get_by_order_id_or_404(self, order_id):
            id = self.model.id_scrambler.backward(order_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    @property
    def order_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('tickets:order', args=[self.order_id])

    def all_tickets(self):
        if self.payment_required():
            tickets = []

            days_for_self = self.unconfirmed_details['days_for_self']
            if days_for_self is not None:
                ticket = UnconfirmedTicket(
                    order=self,
                    owner=self.purchaser,
                    days=days_for_self,
                )
                tickets.append(ticket)

            email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']
            if email_addrs_and_days_for_others is not None:
                for email_addr, days in email_addrs_and_days_for_others:
                    ticket = UnconfirmedTicket(
                        order=self,
                        email_addr=email_addr,
                        days=days,
                    )
                    tickets.append(ticket)
            return tickets
        else:
            return self.tickets.all()

    def form_data(self):
        assert self.payment_required()

        data = {
            'rate': self.rate
        }

        days_for_self = self.unconfirmed_details['days_for_self']
        email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']

        if days_for_self is None:
            assert email_addrs_and_days_for_others is not None
            data['who'] = 'others'
        elif email_addrs_and_days_for_others is None:
            assert days_for_self is not None
            data['who'] = 'self'
        else:
            data['who'] = 'self and others'

        return data

    def self_form_data(self):
        assert self.payment_required()

        days_for_self = self.unconfirmed_details['days_for_self']
        if days_for_self is None:
            return None

        return {'days': days_for_self}

    def others_formset_data(self):
        assert self.payment_required()

        email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']
        if email_addrs_and_days_for_others is None:
            return None

        data = {
            'form-TOTAL_FORMS': str(len(email_addrs_and_days_for_others)),
            'form-INITIAL_FORMS': str(len(email_addrs_and_days_for_others)),
        }

        for ix, (email_addr, days) in enumerate(email_addrs_and_days_for_others):
            data[f'form-{ix}-email_addr'] = email_addr
            data[f'form-{ix}-days'] = days

        return data

    def ticket_details(self):
        return [ticket.details() for ticket in self.all_tickets()]

    def cost(self):
        return sum(ticket.cost() for ticket in self.all_tickets())

    def cost_pence(self):
        return 100 * self.cost()

    def num_tickets(self):
        return len(self.all_tickets())

    def unclaimed_tickets(self):
        return self.tickets.filter(owner=None)

    def payment_required(self):
        return self.status in ['pending', 'failed']


class Ticket(models.Model):
    order = models.ForeignKey(Order, related_name='tickets', on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tickets', null=True, on_delete=models.CASCADE)
    thu = models.BooleanField()
    fri = models.BooleanField()
    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(2000)

    class Manager(models.Manager):
        def get_by_ticket_id_or_404(self, ticket_id):
            id = self.model.id_scrambler.backward(ticket_id)
            return get_object_or_404(self.model, pk=id)

        def create_for_user(self, user, days):
            day_fields = {day: (day in days) for day in DAYS}
            self.create(owner=user, **day_fields)

        def create_with_invitation(self, email_addr, days):
            day_fields = {day: (day in days) for day in DAYS}
            ticket = self.create(**day_fields)
            ticket.invitations.create(email_addr=email_addr)

    objects = Manager()

    @property
    def ticket_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('tickets:ticket', args=[self.ticket_id])

    def details(self):
        return {
            'id': self.ticket_id,
            'name': self.ticket_holder_name(),
            'days': ', '.join(self.days()),
            'cost': self.cost(),
        }

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]

    def ticket_holder_name(self):
        if self.owner:
            return self.owner.name
        else:
            return self.invitation().email_addr

    def cost(self):
        rate = self.order.rate
        return RATES[rate]['ticket_price'] + RATES[rate]['day_price'] * len(self.days())

    def invitation(self):
        # This will raise an exception if a ticket has multiple invitations
        return self.invitations.get()


class UnconfirmedTicket:
    def __init__(self, order, days, owner=None, email_addr=None):
        assert owner or email_addr
        self.order = order
        self.days = [DAYS[day] for day in days]
        self.owner = owner
        self.email_addr = email_addr

    def details(self):
        return {
            'name': self.ticket_holder_name(),
            'days': ', '.join(self.days),
            'cost': self.cost(),
        }

    def ticket_holder_name(self):
        if self.owner:
            return self.owner.name
        else:
            return self.email_addr

    def cost(self):
        rate = self.order.rate
        return RATES[rate]['ticket_price'] + RATES[rate]['day_price'] * len(self.days)


class TicketInvitation(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='invitations', on_delete=models.CASCADE)
    email_addr = models.EmailField()
    token = models.CharField(max_length=12, unique=True)  # An index is automatically created since unique=True
    status = models.CharField(max_length=10, default='unclaimed')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Manager(models.Manager):
        def create(self, **kwargs):
            token = get_random_string(length=12)
            return super().create(token=token, **kwargs)

    objects = Manager()

    def get_absolute_url(self):
        return reverse('tickets:ticket_invitation', args=[self.token])

    def claim_for_owner(self, owner):
        assert self.status == 'unclaimed'
        # TODO where do transactions go?
        ticket = self.ticket
        ticket.owner = owner
        ticket.save()
        self.status = 'claimed'
        self.save()
