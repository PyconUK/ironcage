import stripe

from django.conf import settings


def set_stripe_api_key():
    stripe.api_key = settings.STRIPE_API_KEY_SECRET


def create_charge_for_order(order, token):
    assert order.payment_required()
    set_stripe_api_key()
    return stripe.Charge.create(
        amount=order.cost_pence_incl_vat(),
        currency='gbp',
        description=f'PyCon UK 2017 order {order.order_id}',
        source=token,
        # TODO Should we use include idempotent_key here?
    )
