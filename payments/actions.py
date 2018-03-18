from django.db import transaction

from payments.models import Invoice

import structlog
logger = structlog.get_logger()


def _create_invoice(purchaser, invoice_to, is_credit):
    logger.info('_create_invoice', purchaser=purchaser.id,
                invoice_to=invoice_to)
    with transaction.atomic():
        return Invoice.objects.create(
            purchaser=purchaser,
            invoice_to=invoice_to,
            is_credit=is_credit
        )


def create_new_invoice(purchaser, invoice_to=None):
    logger.info('create_new_invoice', purchaser=purchaser.id,
                invoice_to=invoice_to)
    invoice_to = invoice_to or purchaser.name
    return _create_invoice(purchaser, invoice_to, is_credit=False)


def create_new_credit_note(purchaser, invoice_to=None):
    logger.info('create_new_credit_note', purchaser=purchaser.id,
                invoice_to=invoice_to)
    invoice_to = invoice_to or purchaser.name
    return _create_invoice(purchaser, invoice_to, is_credit=True)
