from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.core.exceptions import ValidationError

from payments.exceptions import (
    InvoiceHasPaymentsException,
    ItemNotOnInvoiceException,
)

import structlog

logger = structlog.get_logger()


STANDARD_RATE_VAT = Decimal(20.0)
ZERO_RATE_VAT = Decimal(0.0)


class SalesRecord(models.Model):

    CREDIT_RECORD = False

    SEQUENCE_PREFIX = ''

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    company_name = models.CharField(max_length=200, null=True, blank=True)
    company_addr = models.TextField(null=True, blank=True)

    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name='%(class)ss',
                                  on_delete=models.PROTECT)

    total_ex_vat = models.DecimalField(max_digits=7, decimal_places=2,
                                       default=Decimal(0.0))

    total_vat = models.DecimalField(max_digits=7, decimal_places=2,
                                    default=Decimal(0.0))

    class Meta:
        abstract = True

    def clean(self):
        if (self.company_name is not None and self.company_addr is None) \
                or (self.company_name is None and self.company_addr is not None):
            raise ValidationError('Both company name and company address must be provided.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def item_id(self):
        return '{}-{}'.format(self.SEQUENCE_PREFIX, self.id)

    def _recalculate_total(self):
        self.total_ex_vat = Decimal(0)
        self.total_vat = Decimal(0)

        for row in self.rows.all():
            if self.CREDIT_RECORD:
                self.total_ex_vat -= row.total_ex_vat
                self.total_vat -= row.total_vat
            else:
                self.total_ex_vat += row.total_ex_vat
                self.total_vat += row.total_vat

        self.total_ex_vat = round(self.total_ex_vat, 2)
        self.total_vat = round(self.total_vat, 2)

        self.save()

    @property
    def total_inc_vat(self):
        return self.total_ex_vat + self.total_vat

    def get_absolute_url(self):
        return reverse('payments:order', args=[self.id])

    @property
    def total_pence_inc_vat(self):
        return int(100 * self.total_inc_vat)

    def add_item(self, item, vat_rate=STANDARD_RATE_VAT):
        logger.info('add invoice row', invoice=self.id, item=item.id,
                    item_type=type(item), vat_rate=vat_rate)

        # Does the invoice have any payments against it?
        if self.payments.count() != 0:
            logger.error('invoice has payments', invoice=self.id)
            raise InvoiceHasPaymentsException

        # TODO: Additional logic regarding:
        # - Only add to credit note if already on paid invoice
        # - Only add to invoice if not already on paid invoice with no
        #   credit notes
        # i.e. ensure each item can be paid for zero or one times

        if type(self) == Invoice:
            row_model = InvoiceRow
        elif type(self) == CreditNote:
            row_model = CreditNoteRow

        with transaction.atomic():
            return row_model.objects.create(
                parent=self,
                item=item,
                total_ex_vat=item.cost_excl_vat(),
                vat_rate=vat_rate
            )

    def delete_item(self, item):
        logger.info('delete invoice row', invoice=self.id, item=item.id,
                    item_type=type(item))

        # Is the item on the invoice?
        # TODO: Make this less crappy
        content_type = ContentType.objects.get_for_model(item)

        rows_with_item = self.rows.filter(
            content_type=content_type,
            object_id=item.id
        ).count()

        if rows_with_item == 0:
            logger.error('item not on invoice', invoice=self.id)
            raise ItemNotOnInvoiceException

        # Does the invoice have any payments against it?
        if self.payments.count() != 0:
            logger.error('invoice has payments', invoice=self.id)
            raise InvoiceHasPaymentsException

        if type(self) == Invoice:
            row_model = InvoiceRow
        elif type(self) == CreditNote:
            row_model = CreditNoteRow

        with transaction.atomic():
            deleted_row = row_model.objects.get(
                parent=self,
                content_type=content_type,
                object_id=item.id
            )

            deleted_row.delete()

    @property
    def payment_required(self):
        # TODO: but is it the right amount?
        return self.payments.filter(
            status=Payment.SUCCESSFUL
        ).count() < 1

    @property
    def successful_payment(self):
        try:
            return self.payments.get(
                status=Payment.SUCCESSFUL
            )
        except Payment.DoesNotExist:
            return None

    def tickets(self):
        from tickets.models import Ticket
        tickets = []

        for row in self.rows.all():
            if isinstance(row.item, Ticket):
                tickets.append(row.item)

        return tickets

    def unclaimed_tickets(self):
        from tickets.models import Ticket, TicketInvitation
        tickets = []

        for row in self.rows.all():
            if isinstance(row.item, Ticket) \
                    and hasattr(row.item, 'invitation') \
                    and row.item.invitation.status == TicketInvitation.UNCLAIMED:
                tickets.append(row.item)

        return tickets

    def brief_summary(self):
        return f'{self.rows.count()} items, £{self.total_inc_vat}'


class SalesRecordRow(models.Model):

    VAT_RATE_CHOICES = (
        (STANDARD_RATE_VAT, 'Standard 20%'),
        (ZERO_RATE_VAT, 'Zero Rated'),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_ex_vat = models.DecimalField(max_digits=7, decimal_places=2)

    vat_rate = models.DecimalField(max_digits=4, decimal_places=2,
                                   choices=VAT_RATE_CHOICES)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_inc_vat(self):
        vat_rate_as_percent = 1 + (self.vat_rate / Decimal(100))
        return self.total_ex_vat * vat_rate_as_percent

    @property
    def total_vat(self):
        vat_rate_as_percent = self.vat_rate / Decimal(100)
        return self.total_ex_vat * vat_rate_as_percent


class Payment(models.Model):

    STRIPE = 'S'

    METHOD_CHOICES = (
        (STRIPE, 'Stripe'),
    )

    SUCCESSFUL = 'SUC'
    FAILED = 'FLD'
    ERRORED = 'ERR'
    REFUNDED = 'RFD'
    CHARGEBACK = 'CBK'

    STATUS_CHOICES = (
        (SUCCESSFUL, 'Successful'),
        (FAILED, 'Failed'),
        (ERRORED, 'Errored'),
        (REFUNDED, 'Refunded'),
        (CHARGEBACK, 'Chargeback'),
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    invoice = models.ForeignKey(SalesRecord, related_name='payments',
                                on_delete=models.PROTECT)

    limit = models.Q(app_label='payments', model='invoice') | \
        models.Q(app_label='payments', model='credit_note')
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING,
                                     limit_choices_to=limit)
    object_id = models.PositiveIntegerField()
    invoice = GenericForeignKey('content_type', 'object_id')

    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    charge_id = models.CharField(max_length=80)
    charge_failure_reason = models.CharField(max_length=400, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    amount = models.DecimalField(max_digits=7, decimal_places=2)


class Invoice(SalesRecord):

    CREDIT_RECORD = False

    SEQUENCE_PREFIX = 'IC-2018'

    payments = GenericRelation(Payment)


class CreditNote(SalesRecord):

    CREDIT_RECORD = True

    SEQUENCE_PREFIX = 'CI-2018'

    CREATED_BY_MISTAKE = 'Mistake'
    REFUNDED_ORDER = 'Refunded'
    ENTITLED_TO_FREE = 'Entitled to Free'
    PAYMENT_BOUNCED = 'Payment Bounced'
    CHARGEBACK = 'Chargeback'
    WRONG_TICKET_TYPE = 'Wrong ticket type'
    ATTENDANCE_REFUSED = 'Attendance Refused'
    COC_BREACH = 'Breach of CoC'
    VISA_ISSUES = 'Issues with travel Visa'
    TRAVEL_ISSUES = 'Issues with travel'
    ACCOMMODATION_ISSUES = 'Issues with accommodation'

    REASON_CHOICES = (
        (CREATED_BY_MISTAKE, 'Order created by mistake'),
        (REFUNDED_ORDER, 'Purchaser requested refund'),
        (ENTITLED_TO_FREE, 'Purchaser entitled to a free ticket'),
        (PAYMENT_BOUNCED, 'Payment did not complete'),
        (CHARGEBACK, 'Payment chargeback received'),
        (WRONG_TICKET_TYPE, 'Ticket booked was of wrong type'),
        (ATTENDANCE_REFUSED, 'Organisers or venue denied entry'),
        (COC_BREACH, 'Organisers removed attendee from conference'),
        (VISA_ISSUES, 'Attendee could not get travel visa'),
        (TRAVEL_ISSUES, 'Attendee could not arrange travel to conference'),
        (ACCOMMODATION_ISSUES, 'Attendee could not attend conference due lack of available accommodation'),
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.DO_NOTHING,
                                related_name='credit_note')

    reason = models.CharField(max_length=30, choices=REASON_CHOICES, blank=False, null=False)

    payments = GenericRelation(Payment)


class InvoiceRow(SalesRecordRow):

    parent = models.ForeignKey(Invoice, related_name='rows',
                               on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ("parent", "content_type", "object_id")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parent._recalculate_total()

    def delete(self, *args, **kwargs):
        parent = self.parent
        super().delete(*args, **kwargs)
        parent._recalculate_total()


class CreditNoteRow(SalesRecordRow):

    parent = models.ForeignKey(CreditNote, related_name='rows',
                               on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ("parent", "content_type", "object_id")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.parent._recalculate_total()

    def delete(self, *args, **kwargs):
        parent = self.parent
        super().delete(*args, **kwargs)
        parent._recalculate_total()
