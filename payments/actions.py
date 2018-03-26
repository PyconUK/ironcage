import stripe

from django.db import transaction

from payments.models import Invoice, Payment

from django.db.utils import IntegrityError

from payments.stripe_integration import create_charge_for_invoice

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


def confirm_order(order, charge_id, charge_created):
    logger.info('confirm_order', invoice=invoice.id, charge_id=charge_id)
    with transaction.atomic():
        invoice.confirm(charge_id, charge_created)
    send_receipt(invoice)
    send_ticket_invitations(invoice)
    slack_message('tickets/order_created.slack', {'invoice': invoice})


def process_stripe_charge(invoice, token):
    logger.info('process_stripe_charge', invoice=invoice.invoice_id, token=token)
    assert invoice.payment_required
    try:
        charge = create_charge_for_invoice(invoice, token)
        Payment.objects.create(
            invoice=invoice,
            method=Payment.STRIPE,
            status=Payment.SUCCESSFUL,
            charge_id=charge.id,
            amount=charge.amount/100
        )

        confirm_order(invoice, charge.id, charge.created)
    except stripe.error.CardError as e:
        mark_order_as_failed(invoice, e._message)
    except IntegrityError:
        refund_charge(charge.id)
        mark_order_as_errored_after_charge(invoice, charge.id)


def send_receipt(order):
    logger.info('send_receipt', order=order.order_id)
    send_order_confirmation_mail(order)


def send_ticket_invitations(order):
    logger.info('send_ticket_invitations', order=order.order_id)
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket)
