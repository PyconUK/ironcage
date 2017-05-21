import stripe

from django.conf import settings


def set_stripe_api_key():
    stripe.api_key = settings.STRIPE_API_KEY


def create_charge_for_order(order, token):
    assert order.status in ['pending', 'failed'], f'Unexpected status for order {order.order_id}: {order.status}'
    set_stripe_api_key()
    try:
        charge = stripe.Charge.create(
            amount=order.cost_pence(),
            currency='gbp',
            description=f'PyCon UK 2017 order {order.order_id}',
            source=token,
            # TODO Should we use include idempotent_key here?
        )
        order.stripe_charge_id = charge.id
        order.stripe_charge_failure_reason = ''
        order.status = 'successful'
    except stripe.error.CardError as e:
        order.stripe_charge_failure_reason = e._message
        order.status = 'failed'

    order.save()
