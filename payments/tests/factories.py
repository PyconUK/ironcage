import random
import string


from accounts.tests.factories import create_user

from payments import actions
from payments.models import STANDARD_RATE_VAT, Payment
from tickets.tests.factories import (
    create_ticket
)


def create_invoice(user=None, invoice_to=None):
    user = user or create_user()
    invoice_to = invoice_to or user.name

    return actions.create_new_invoice(
        purchaser=user,
        invoice_to=invoice_to
    )


def create_credit_note(user=None, invoice_to=None):
    user = user or create_user()
    invoice_to = invoice_to or user.name

    return actions.create_new_credit_note(
        purchaser=user,
        invoice_to=invoice_to
    )


def add_invoice_row(item=None, user=None, invoice=None, vat_rate=None):
    user = user or create_user()
    invoice = invoice or create_invoice(user)
    item = item or create_ticket(user)
    vat_rate = vat_rate if vat_rate is not None else STANDARD_RATE_VAT

    return invoice.add_row(
        item=item,
        vat_rate=vat_rate
    )


def make_payment(invoice=None, status=None, amount=None):
    invoice = invoice or create_invoice(create_user())
    status = status or Payment.SUCCESSFUL
    amount = amount or invoice.total

    return Payment.objects.create(
        invoice=invoice,
        method=Payment.STRIPE,
        status=status,
        charge_id=''.join(random.sample(string.ascii_letters, 10)),
        amount=amount
    )
