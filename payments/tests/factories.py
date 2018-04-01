import random
import string


from accounts.tests.factories import create_user

from payments import actions
from payments.models import STANDARD_RATE_VAT, Payment, CreditNote
from tickets.tests.factories import (
    create_ticket
)


def create_invoice(user=None, company_name=None, company_addr=None):
    user = user or create_user()

    return actions.create_new_invoice(
        purchaser=user,
        company_name=company_name,
        company_addr=company_addr,
    )


def create_credit_note(user=None, invoice=None, company_name=None, company_addr=None):
    user = user or create_user()

    return actions.create_new_credit_note(
        purchaser=user,
        reason=CreditNote.CREATED_BY_MISTAKE,
        invoice=invoice,
        company_name=company_name,
        company_addr=company_addr,
    )


def add_invoice_item(item=None, user=None, invoice=None, vat_rate=None):
    user = user or create_user()
    invoice = invoice or create_invoice(user)
    item = item or create_ticket(user)
    vat_rate = vat_rate if vat_rate is not None else STANDARD_RATE_VAT

    return invoice.add_item(
        item=item,
        vat_rate=vat_rate
    )


def delete_invoice_item(item=None, user=None, invoice=None):
    user = user or create_user()
    invoice = invoice or create_invoice(user)
    item = item or create_ticket(user)

    return invoice.delete_item(
        item=item
    )


def make_payment(invoice=None, status=None, amount=None):
    invoice = invoice or create_invoice(create_user())
    status = status or Payment.SUCCESSFUL
    amount = amount or invoice.total_inc_vat

    return Payment.objects.create(
        invoice=invoice,
        method=Payment.STRIPE,
        status=status,
        charge_id=''.join(random.sample(string.ascii_letters, 10)),
        amount=amount
    )
