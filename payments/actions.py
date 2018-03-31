import structlog

import stripe

from django.db import transaction
from django.db.utils import IntegrityError

from payments.models import (
    CreditNote,
    Invoice,
    Payment,
)
from payments.stripe_integration import create_charge_for_invoice

from tickets.mailer import send_order_confirmation_mail, send_invitation_mail
from django_slack import slack_message

logger = structlog.get_logger()


def create_new_invoice(purchaser, company_name=None, company_addr=None):
    logger.info('create_new_invoice', purchaser=purchaser.id,
                company_name=company_name, company_addr=company_addr)

    with transaction.atomic():
        return Invoice.objects.create(
            purchaser=purchaser,
            company_name=company_name,
            company_addr=company_addr,
        )


def create_new_credit_note(purchaser, invoice, reason,
                           company_name=None, company_addr=None):
    logger.info('create_new_credit_note', purchaser=purchaser.id,
                invoice=invoice.item_id, reason=reason,
                company_name=company_name, company_addr=company_addr)

    with transaction.atomic():
        return CreditNote.objects.create(
            purchaser=purchaser,
            invoice=invoice,
            reason=reason,
            company_name=company_name,
            company_addr=company_addr,
        )


def confirm_invoice(invoice, charge_id, charge_created):
    logger.info('confirm_invoice', invoice=invoice.id, charge_id=charge_id)
    # with transaction.atomic():
    # This used to actually register the stripe charge in the DB and create tickets
    #     invoice.confirm(charge_id, charge_created)
    send_receipt(invoice)
    send_ticket_invitations(invoice)
    slack_message('tickets/order_created.slack', {'invoice': invoice})


def mark_payment_as_failed(invoice, failure_message):
    with transaction.atomic():
        return Payment.objects.create(
            invoice=invoice,
            method=Payment.STRIPE,
            status=Payment.FAILED,
            charge_failure_reason=failure_message,
        )


def mark_payment_as_errored_after_charge(invoice, charge_id, charge_amount):
    with transaction.atomic():
        return Payment.objects.create(
            invoice=invoice,
            method=Payment.STRIPE,
            status=Payment.ERRORED,
            charge_id=charge_id,
            amount=charge_amount/100
        )


def process_stripe_charge(invoice, token):
    logger.info('process_stripe_charge', invoice=invoice.item_id, token=token)
    assert invoice.payment_required
    try:
        # This registers the payment we just got with stripe
        charge = create_charge_for_invoice(invoice, token)

        # Then we record it locally
        with transaction.atomic():
            payment = Payment.objects.create(
                invoice=invoice,
                method=Payment.STRIPE,
                status=Payment.SUCCESSFUL,
                charge_id=charge.id,
                amount=charge.amount/100
            )

        # Then we run any additional tasks
        confirm_invoice(invoice, charge.id, charge.created)

        return payment

    except stripe.error.CardError as e:
        return mark_payment_as_failed(invoice, e._message)

    except IntegrityError:
        refund_charge(charge.id)

        mark_payment_as_errored_after_charge(invoice, charge.id. charge.amount)


def send_receipt(order):
    logger.info('send_receipt', order=order.item_id)
    send_order_confirmation_mail(order)


def send_ticket_invitations(order):
    logger.info('send_ticket_invitations', order=order.item_id)
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket)
