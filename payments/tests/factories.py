from accounts.tests.factories import create_user

from payments import actions
from payments.models import STANDARD_RATE_VAT
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


def add_invoice_row(item=None, user=None, invoice=None, vat_rate=None):
    user = user or create_user()
    invoice = invoice or create_invoice(user)
    item = item or create_ticket(user)
    vat_rate = vat_rate if vat_rate is not None else STANDARD_RATE_VAT

    return invoice.add_row(
        item=item,
        vat_rate=vat_rate
    )
