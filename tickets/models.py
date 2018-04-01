from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

from ironcage.utils import Scrambler

from .constants import DAYS
from .prices import cost_excl_vat, cost_incl_vat

from payments.models import Invoice


class Ticket(models.Model):

    INDIVIDUAL = 'INDI'
    CORPORATE = 'CORP'
    EDUCATION = 'EDUC'
    FREE = 'FREE'

    RATE_CHOICES = (
        (INDIVIDUAL, 'Individual'),
        (CORPORATE, 'Corporate'),
        (EDUCATION, 'Educational'),
        (FREE, 'Free'),
    )

    pot = models.CharField(max_length=100, null=True, blank=True)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, null=True,
                                 on_delete=models.DO_NOTHING, related_name='ticket')
    rate = models.CharField(max_length=4, choices=RATE_CHOICES, blank=False, null=False)
    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()
    tue = models.BooleanField()
    wed = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(2000)

    class Manager(models.Manager):
        @staticmethod
        def _check_days(days):
            return isinstance(days, list) \
                   and len(days) > 0 \
                   and all(day in DAYS for day in days)

        def get_by_ticket_id_or_404(self, ticket_id):
            id = self.model.id_scrambler.backward(ticket_id)
            return get_object_or_404(self.model, pk=id)

        def create_for_user(self, user, rate, days):
            if not self._check_days(days):
                raise ValidationError('Please provide at least one day')

            day_fields = {day: (day in days) for day in DAYS}
            return self.create(owner=user, rate=rate, **day_fields)

        def create_with_invitation(self, email_addr, rate, days):
            if not self._check_days(days):
                raise ValidationError('Please provide at least one day')

            day_fields = {day: (day in days) for day in DAYS}
            ticket = self.create(rate=rate, owner=None, **day_fields)
            TicketInvitation.objects.create(
                ticket=ticket, email_addr=email_addr
            )
            return ticket

        def create_free_with_invitation(self, email_addr, pot):
            days = {day: False for day in DAYS}
            ticket = self.create(pot=pot, rate=Ticket.FREE, **days)
            TicketInvitation.objects.create(
                ticket=ticket, email_addr=email_addr
            )
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
            invitation = self.invitation
            invitation.delete()
        except TicketInvitation.DoesNotExist:
            pass

        TicketInvitation.objects.create(
            ticket=self, email_addr=email_addr
        )

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
        return self.invitations.get() if self.invitations.count() else None

    def is_free_ticket(self):
        return self.rate == self.FREE
        # Previously checked for an order being attached

    def is_incomplete(self):
        return self.days() == []

    def update_days(self, days):
        for day in DAYS:
            setattr(self, day, (day in days))
        self.save()

    @property
    def valid(self):
        if self.rate == self.FREE:
            return True
        else:
            return False

    @property
    def item_id(self):
        return self.ticket_id

    @property
    def invoice_description(self):
        return 'PyCon UK 2018 Ticket for {} ({})'.format(
            self.invitation.email_addr if hasattr(self, 'invitation') else self.owner,
            ', '.join(self.days()),
        )

    @property
    def invoice(self):
        # TODO: Better
        content_type = ContentType.objects.get_for_model(Ticket)
        return Invoice.objects.filter(
            rows__content_type=content_type,
            rows__object_id=self.id
        ).first()


class TicketInvitation(models.Model):

    UNCLAIMED = 'U'
    CLAIMED = 'C'

    STATUS_CHOICES = (
        (UNCLAIMED, 'Unclaimed'),
        (CLAIMED, 'Claimed'),
    )

    ticket = models.OneToOneField(Ticket, related_name='invitation', on_delete=models.CASCADE)  # This should be a OneToOneField
    email_addr = models.EmailField(unique=True)
    token = models.CharField(max_length=12, unique=True)  # An index is automatically created since unique=True
    status = models.CharField(max_length=1, default=UNCLAIMED, choices=STATUS_CHOICES)

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
        assert self.status == self.UNCLAIMED
        ticket = self.ticket
        ticket.owner = owner
        ticket.save()
        self.status = self.CLAIMED
        self.save()
