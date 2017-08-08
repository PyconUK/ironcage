from django_slack import slack_message
import stripe

from django.db import transaction

from ironcage.stripe_integration import create_charge_for_order

from .mailer import send_order_confirmation_mail
from .models import Order

import structlog
logger = structlog.get_logger()


def create_pending_order(purchaser, adult_name, adult_email_addr, adult_phone_number, accessibility_reqs, dietary_reqs, unconfirmed_details):
    logger.info('children.actions.create_pending_order', purchaser=purchaser.id)
    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser=purchaser,
            adult_name=adult_name,
            adult_phone_number=adult_phone_number,
            adult_email_addr=adult_email_addr,
            accessibility_reqs=accessibility_reqs,
            dietary_reqs=dietary_reqs,
            unconfirmed_details=unconfirmed_details,
        )


def update_pending_order(order, adult_name, adult_email_addr, adult_phone_number, accessibility_reqs, dietary_reqs, unconfirmed_details):
    logger.info('children:update_pending_order', order=order.order_id)
    with transaction.atomic():
        order.update(adult_name, adult_email_addr, adult_phone_number, accessibility_reqs, dietary_reqs, unconfirmed_details)


def process_stripe_charge(order, token):
    logger.info('children:process_stripe_charge', order=order.order_id, token=token)
    assert order.payment_required()
    try:
        charge = create_charge_for_order(order, token)
        confirm_order(order, charge.id, charge.created)
    except stripe.error.CardError as e:
        mark_order_as_failed(order, e._message)


def confirm_order(order, charge_id, charge_created):
    logger.info('children:confirm_order', order=order.order_id, charge_id=charge_id)
    with transaction.atomic():
        order.confirm(charge_id, charge_created)
    send_receipt(order)
    slack_message('children/order_created.slack', {'order': order})


def mark_order_as_failed(order, charge_failure_reason):
    logger.info('children:mark_order_as_failed', order=order.order_id, charge_failure_reason=charge_failure_reason)
    with transaction.atomic():
        order.mark_as_failed(charge_failure_reason)


def send_receipt(order):
    logger.info('children:children:send_receipt', order=order.order_id)
    send_order_confirmation_mail(order)
