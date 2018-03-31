from collections import defaultdict
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

from ironcage.utils import Scrambler

from .constants import DAYS
from .prices import cost_excl_vat, cost_incl_vat


class Order(models.Model):
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    rate = models.CharField(max_length=40)
    company_name = models.CharField(max_length=200, null=True)
    company_addr = models.TextField(null=True)
    status = models.CharField(max_length=10)
    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_created = models.DateTimeField(null=True)
    stripe_charge_failure_reason = models.CharField(max_length=400, blank=True)
    unconfirmed_details = JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(1000)

    class Manager(models.Manager):
        def get_by_order_id_or_404(self, order_id):
            id = self.model.id_scrambler.backward(order_id)
            return get_object_or_404(self.model, pk=id)

        def create_pending(self, purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
            assert days_for_self is not None or email_addrs_and_days_for_others is not None

            if rate == 'corporate':
                assert company_details is not None
                company_name = company_details['name']
                company_addr = company_details['addr']
            elif rate in ['individual', 'education']:
                assert company_details is None
                company_name = None
                company_addr = None
            else:
                assert False

            unconfirmed_details = {
                'days_for_self': days_for_self,
                'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
            }

            return self.create(
                purchaser=purchaser,
                rate=rate,
                company_name=company_name,
                company_addr=company_addr,
                status='pending',
                unconfirmed_details=unconfirmed_details,
            )

    objects = Manager()

    def __str__(self):
        return self.order_id

    @property
    def order_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('tickets:order', args=[self.order_id])

    def update(self, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
        assert self.payment_required()
        assert days_for_self is not None or email_addrs_and_days_for_others is not None

        if rate == 'corporate':
            assert company_details is not None
            self.company_name = company_details['name']
            self.company_addr = company_details['addr']
        elif rate in ['individual', 'education']:
            assert company_details is None
            self.company_name = None
            self.company_addr = None
        else:
            assert False

        self.rate = rate
        self.unconfirmed_details = {
            'days_for_self': days_for_self,
            'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
        }
        self.save()

    def confirm(self, charge_id, charge_created):
        assert self.payment_required()

        days_for_self = self.unconfirmed_details['days_for_self']
        if days_for_self is not None:
            self.tickets.create_for_user(self.purchaser, self.rate, days_for_self)

        email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']
        if email_addrs_and_days_for_others is not None:
            for email_addr, days in email_addrs_and_days_for_others:
                self.tickets.create_with_invitation(email_addr, self.rate,  days)

        self.stripe_charge_id = charge_id
        self.stripe_charge_created = datetime.fromtimestamp(charge_created, tz=timezone.utc)
        self.stripe_charge_failure_reason = ''
        self.status = 'successful'

        self.save()

    def mark_as_failed(self, charge_failure_reason):
        self.stripe_charge_failure_reason = charge_failure_reason
        self.status = 'failed'

        self.save()

    def march_as_errored_after_charge(self, charge_id):
        self.stripe_charge_id = charge_id
        self.stripe_charge_failure_reason = ''
        self.status = 'errored'

        self.save()

    def delete_tickets_and_mark_as_refunded(self):
        self.tickets.all().delete()
        self.status = 'refunded'

        self.save()

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
            return self.tickets.order_by('id')

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

    def company_details_form_data(self):
        if self.rate == 'corporate':
            return {
                'company_name': self.company_name,
                'company_addr': self.company_addr,
            }
        else:
            return None

    def ticket_details(self):
        return [ticket.details() for ticket in self.all_tickets()]

    def ticket_summary(self):
        num_tickets_by_num_days = defaultdict(int)

        for ticket in self.all_tickets():
            num_tickets_by_num_days[ticket.num_days()] += 1

        summary = []

        for ix in range(5):
            num_days = ix + 1
            if num_tickets_by_num_days[num_days]:
                num_tickets = num_tickets_by_num_days[num_days]
                summary.append({
                    'num_days': num_days,
                    'num_tickets': num_tickets,
                    'per_item_cost_excl_vat': cost_excl_vat(self.rate, num_days),
                    'per_item_cost_incl_vat': cost_incl_vat(self.rate, num_days),
                    'total_cost_excl_vat': cost_excl_vat(self.rate, num_days) * num_tickets,
                    'total_cost_incl_vat': cost_incl_vat(self.rate, num_days) * num_tickets,
                })

        return summary

    def brief_summary(self):
        summary = f'{self.num_tickets()} {self.rate}-rate ticket'
        if self.num_tickets() > 1:
            summary += 's'
        return summary

    def cost_excl_vat(self):
        return sum(ticket.cost_excl_vat() for ticket in self.all_tickets())

    def cost_incl_vat(self):
        return sum(ticket.cost_incl_vat() for ticket in self.all_tickets())

    def vat(self):
        return self.cost_incl_vat() - self.cost_excl_vat()

    def cost_pence_incl_vat(self):
        return 100 * self.cost_incl_vat()

    def num_tickets(self):
        return len(self.all_tickets())

    def unclaimed_tickets(self):
        return self.tickets.filter(owner=None)

    def ticket_for_self(self):
        tickets = [ticket for ticket in self.all_tickets() if ticket.owner == self.purchaser]
        if len(tickets) == 0:
            return None
        elif len(tickets) == 1:
            return tickets[0]
        else:
            assert False

    def tickets_for_others(self):
        return [ticket for ticket in self.all_tickets() if ticket.owner != self.purchaser]

    def payment_required(self):
        return self.status in ['pending', 'failed']

    def company_addr_formatted(self):
        if self.rate == 'corporate':
            lines = [line.strip(',') for line in self.company_addr.splitlines() if line]
            return ', '.join(lines)
        else:
            return None


class Ticket(models.Model):
    # order = models.ForeignKey(Order, related_name='tickets', null=True, on_delete=models.CASCADE)
    pot = models.CharField(max_length=100, null=True)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    rate = models.CharField(max_length=40)
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

        def create_for_user(self, user, rate, days):
            day_fields = {day: (day in days) for day in DAYS}
            return self.create(owner=user, rate=rate, **day_fields)

        def create_with_invitation(self, email_addr, rate, days):
            day_fields = {day: (day in days) for day in DAYS}
            ticket = self.create(rate=rate, **day_fields)
            ticket.invitations.create(email_addr=email_addr)
            return ticket

        def create_free_with_invitation(self, email_addr, pot):
            days = {day: False for day in DAYS}
            ticket = self.create(pot=pot, **days)
            ticket.invitations.create(email_addr=email_addr)
            return ticket

    objects = Manager()

    def __str__(self):
        return self.ticket_id

    @property
    def ticket_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('tickets:ticket', args=[self.ticket_id])

    def reassign(self, email_addr):
        if self.owner is not None:
            self.owner = None
            self.save()

        try:
            invitation = self.invitation()
            invitation.delete()
        except TicketInvitation.DoesNotExist:
            pass

        self.invitations.create(email_addr=email_addr)

    def details(self):
        return {
            'id': self.ticket_id,
            'name': self.ticket_holder_name(),
            'days': ', '.join(self.days()),
            'cost_excl_vat': self.cost_excl_vat(),
            'cost_incl_vat': self.cost_incl_vat(),
        }

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]

    def days_abbrev(self):
        return [day for day in DAYS if getattr(self, day)]

    def num_days(self):
        return len(self.days())

    def ticket_holder_name(self):
        if self.owner:
            return self.owner.name
        else:
            return self.invitation().email_addr

    # def rate(self):
    #     if self.order is None:
    #         return 'free'
    #     else:
    #         return self.order.rate

    def cost_incl_vat(self):
        return cost_incl_vat(self.rate, self.num_days())

    def cost_excl_vat(self):
        return cost_excl_vat(self.rate, self.num_days())

    def invitation(self):
        # This will raise an exception if a ticket has multiple invitations
        return self.invitations.get()

    def is_free_ticket(self):
        return self.rate == 'free'
        # Previously checked for an order being attached

    def is_incomplete(self):
        return self.days() == []

    def update_days(self, days):
        for day in DAYS:
            setattr(self, day, (day in days))
        self.save()

    @property
    def item_id(self):
        return self.ticket_id

    @property
    def invoice_description(self):
        return 'PyCon UK 2018 Ticket for {} ({})'.format(
            self.invitation().email_addr if self.invitation() else self.owner,
            ', '.join(self.days()),
        )


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
            'cost_excl_vat': self.cost_excl_vat(),
            'cost_incl_vat': self.cost_incl_vat(),
        }

    def num_days(self):
        return len(self.days)

    def ticket_holder_name(self):
        if self.owner:
            return self.owner.name
        else:
            return self.email_addr

    def cost_incl_vat(self):
        return cost_incl_vat(self.order.rate, self.num_days())

    def cost_excl_vat(self):
        return cost_excl_vat(self.order.rate, self.num_days())


class TicketInvitation(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='invitations', on_delete=models.CASCADE)  # This should be a OneToOneField
    email_addr = models.EmailField()  # This should be unique=True
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
        # This would fail if owner already has a ticket, as Ticket.owner is a
        # OneToOneField.
        assert self.status == 'unclaimed'
        ticket = self.ticket
        ticket.owner = owner
        ticket.save()
        self.status = 'claimed'
        self.save()
