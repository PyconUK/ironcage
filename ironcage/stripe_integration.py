import stripe

from django.conf import settings


def set_stripe_api_key():
    stripe.api_key = settings.STRIPE_API_KEY_SECRET


def create_charge(amount_pence, description, token):
    set_stripe_api_key()
    return stripe.Charge.create(
        amount=amount_pence,
        currency='gbp',
        description=description,
        statement_descriptor=description,
        source=token,
    )


def create_charge_for_order(order, token):
    assert order.payment_required()
    return create_charge(
        order.cost_pence_incl_vat(),
        f'PyCon UK 2017 order {order.order_id}',
        token,
    )


def refund_charge(charge_id):
    set_stripe_api_key()
    stripe.Refund.create(charge=charge_id)
