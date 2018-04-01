import structlog

import stripe

from django.db import transaction
from django.db.utils import IntegrityError
from django_slack import slack_message

from payments.exceptions import InvoiceAlreadyPaidException
from payments.models import (
    CreditNote,
    Invoice,
    Payment,
)
from payments.stripe_integration import (
    create_charge_for_invoice,
    refund_charge,
)
from tickets.mailer import (
    send_invitation_mail,
    send_order_confirmation_mail,
)

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


def create_failed_payment(invoice, failure_message, charge_id):
    with transaction.atomic():
        return Payment.objects.create(
            invoice=invoice,
            method=Payment.STRIPE,
            status=Payment.FAILED,
            charge_failure_reason=failure_message,
            charge_id=charge_id,
            amount=0
        )


def create_errored_after_charge_payment(invoice, charge_id, charge_amount, method=Payment.STRIPE):
    with transaction.atomic():
        return Payment.objects.create(
            invoice=invoice,
            method=method,
            status=Payment.ERRORED,
            charge_id=charge_id,
            amount=charge_amount/100
        )


def create_successful_payment(invoice, charge_id, charge_amount, method=Payment.STRIPE):
    with transaction.atomic():
        return Payment.objects.create(
            invoice=invoice,
            method=method,
            status=Payment.SUCCESSFUL,
            charge_id=charge_id,
            amount=charge_amount/100
        )


def pay_invoice_by_stripe(invoice, stripe_token):
    logger.info('pay_invoice_by_stripe', invoice=invoice.item_id, token=stripe_token)
    if invoice.successful_payment:
        raise InvoiceAlreadyPaidException
    else:
        try:
            # This registers the payment we just got with stripe
            charge = create_charge_for_invoice(invoice, stripe_token)

            # Then we record it locally
            payment = create_successful_payment(invoice, charge.id, charge.amount)

            # Then we run any additional tasks
            confirm_invoice(invoice, charge.id, charge.created)

            return payment

        except stripe.error.CardError as e:
            # This is where stripe errors - a FAILED transaction
            charge_id = e.json_body['error']['charge']
            return create_failed_payment(invoice, e._message, charge_id)

        except IntegrityError:
            # This is where we errors - an ERRORED transaction
            # As this is our fault, we've already taken the payment from the
            # customer and should refund the charge
            refund_charge(charge.id)

            return create_errored_after_charge_payment(invoice, charge.id, charge.amount)


def send_receipt(order):
    logger.info('send_receipt', order=order.item_id)
    send_order_confirmation_mail(order)


def send_ticket_invitations(order):
    logger.info('send_ticket_invitations', order=order.item_id)
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket)
