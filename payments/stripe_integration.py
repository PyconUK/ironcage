import stripe

from django.conf import settings


def set_stripe_api_key():
    stripe.api_key = settings.STRIPE_API_KEY_SECRET


def create_charge(amount_pence, description, statement_descriptor, token):
    assert len(statement_descriptor) <= 22
    set_stripe_api_key()
    return stripe.Charge.create(
        amount=amount_pence,
        currency='gbp',
        description=description,
        statement_descriptor=statement_descriptor,
        source=token,
    )


def create_charge_for_invoice(invoice, token):
    # assert invoice.payment_required()
    return create_charge(
        invoice.total_pence_inc_vat,
        f'PyCon UK invoice 2018-{invoice.id}',
        f'PyCon UK 2018-{invoice.id}',
        token,
    )


def refund_charge(charge_id):
    set_stripe_api_key()
    stripe.Refund.create(charge=charge_id)
