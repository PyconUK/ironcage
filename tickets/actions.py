import stripe

from django.db import transaction

from .mailer import send_invitation_mail, send_order_confirmation_mail
from .models import Order
from .stripe_integration import create_charge_for_order


def create_pending_order(purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            rate,
            days_for_self,
            email_addrs_and_days_for_others,
            company_details=company_details,
        )


def update_pending_order(order, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    with transaction.atomic():
        order.update(rate, days_for_self, email_addrs_and_days_for_others, company_details)


def process_stripe_charge(order, token):
    assert order.payment_required()
    try:
        charge = create_charge_for_order(order, token)
        confirm_order(order, charge.id, charge.created)
    except stripe.error.CardError as e:
        mark_order_as_failed(order, e._message)


def confirm_order(order, charge_id, charge_created):
    with transaction.atomic():
        order.confirm(charge_id, charge_created)
    send_receipt(order)
    send_ticket_invitations(order)


def mark_order_as_failed(order, charge_failure_reason):
    with transaction.atomic():
        order.mark_as_failed(charge_failure_reason)


def send_receipt(order):
    send_order_confirmation_mail(order)


def send_ticket_invitations(order):
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket.invitation())


def claim_ticket_invitation(owner, invitation):
    with transaction.atomic():
        invitation.claim_for_owner(owner)
