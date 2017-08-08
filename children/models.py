from datetime import datetime, timezone

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ironcage.utils import Scrambler


class Order(models.Model):
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='children_orders', on_delete=models.CASCADE)
    adult_name = models.CharField(max_length=255)
    adult_email_addr = models.CharField(max_length=255)
    adult_phone_number = models.CharField(max_length=255)
    accessibility_reqs = models.TextField(null=True, blank=True)
    dietary_reqs = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10)
    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_created = models.DateTimeField(null=True)
    stripe_charge_failure_reason = models.CharField(max_length=400, blank=True)
    unconfirmed_details = JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(6000)

    class Manager(models.Manager):
        def get_by_order_id_or_404(self, order_id):
            id = self.model.id_scrambler.backward(order_id)
            return get_object_or_404(self.model, pk=id)

        def create_pending(self, purchaser, adult_name, adult_email_addr, adult_phone_number, accessibility_reqs, dietary_reqs, unconfirmed_details):
            assert len(unconfirmed_details) > 0

            return self.create(
                purchaser=purchaser,
                adult_name=adult_name,
                adult_phone_number=adult_phone_number,
                adult_email_addr=adult_email_addr,
                accessibility_reqs=accessibility_reqs,
                dietary_reqs=dietary_reqs,
                unconfirmed_details=unconfirmed_details,
                status='pending',
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
        return reverse('children:order', args=[self.order_id])

    def update(self, adult_name, adult_email_addr, adult_phone_number, accessibility_reqs, dietary_reqs, unconfirmed_details):
        assert self.payment_required()
        assert len(unconfirmed_details) > 0

        self.adult_name = adult_name
        self.adult_phone_number = adult_phone_number
        self.adult_email_addr = adult_email_addr
        self.accessibility_reqs = accessibility_reqs
        self.dietary_reqs = dietary_reqs
        self.unconfirmed_details = unconfirmed_details

        self.save()

    def confirm(self, charge_id, charge_created):
        assert self.payment_required()

        for name, date_of_birth in self.unconfirmed_details:
            self.tickets.create(name=name, date_of_birth=date_of_birth)

        self.stripe_charge_id = charge_id
        self.stripe_charge_created = datetime.fromtimestamp(charge_created, tz=timezone.utc)
        self.stripe_charge_failure_reason = ''
        self.status = 'successful'

        self.save()

    def mark_as_failed(self, charge_failure_reason):
        self.stripe_charge_failure_reason = charge_failure_reason
        self.status = 'failed'

        self.save()

    def payment_required(self):
        return self.status in ['pending', 'failed']

    def num_tickets(self):
        return len(self.all_tickets())

    def cost_incl_vat(self):
        return 5 * self.num_tickets()

    def cost_pence_incl_vat(self):
        return 100 * self.cost_incl_vat()

    def all_tickets(self):
        if self.payment_required():
            tickets = []
            for name, date_of_birth in self.unconfirmed_details:
                ticket = Ticket(name=name, date_of_birth=date_of_birth)
                tickets.append(ticket)
            return tickets
        else:
            return self.tickets.all()

    def ticket_details(self):
        return [ticket.details() for ticket in self.all_tickets()]


class Ticket(models.Model):
    order = models.ForeignKey(Order, related_name='tickets', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(7000)

    class Manager(models.Manager):
        def get_by_ticket_id_or_404(self, ticket_id):
            id = self.model.id_scrambler.backward(ticket_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    def __str__(self):
        return self.ticket_id

    @property
    def ticket_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def details(self):
        return {
            'name': self.name,
            'date_of_birth': self.date_of_birth,
        }
