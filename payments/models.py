from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from ironcage.utils import Scrambler

STANDARD_RATE_VAT = 20.0
ZERO_RATE_VAT = 0.0


class Invoice(models.Model):

    id_scrambler = Scrambler(10000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  related_name='invoices',
                                  on_delete=models.PROTECT)

    invoice_to = models.TextField()

    is_credit = models.BooleanField()

    total = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)


    def add_row(self, item, vat_rate=STANDARD_RATE_VAT):
        logger.info('add invoice row', invoice=self.id, item=item.id,
                    item_type=type(item), vat_rate=vat_rate)

        with transaction.atomic():
            InvoiceRow.objects.create(
                invoice=self,
                invoice_item=item,
                total_ex_vat=item.cost_excl_vat(),
                vat_rate=vat_rate
            )


class InvoiceRow(models.Model):

    VAT_RATE_CHOICES = (
        (STANDARD_RATE_VAT, 'Standard 20%'),
        (ZERO_RATE_VAT, 'Zero Rated'),
    )

    invoice = models.ForeignKey(Invoice, related_name='rows',
                                on_delete=models.PROTECT)

    object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    invoice_item = GenericForeignKey('object_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_ex_vat = models.DecimalField(max_digits=7, decimal_places=2)

    vat_rate = models.DecimalField(max_digits=4, decimal_places=2,
                                   choices=VAT_RATE_CHOICES)


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

    id_scrambler = Scrambler(20000)

    invoice = models.ForeignKey(Invoice, related_name='invoice',
                                on_delete=models.PROTECT)

    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    charge_id = models.CharField(max_length=80)
    charge_created = models.DateTimeField(null=True)
    charge_failure_reason = models.CharField(max_length=400, blank=True)

    amount = models.DecimalField(max_digits=7, decimal_places=2)
