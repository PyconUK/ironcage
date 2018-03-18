from accounts.tests.factories import create_user

from payments import actions


def create_invoice(user=None, invoice_to=None):
    user = user or create_user()
    invoice_to = invoice_to or user.name

    return actions.create_new_invoice(
        purchaser=user,
        invoice_to=invoice_to
    )
