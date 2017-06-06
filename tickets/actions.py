import stripe

from .invitation_mailer import send_invitation_mail
from .models import Order
from .stripe_integration import create_charge_for_order


def create_pending_order(purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    return Order.objects.create_pending(purchaser, rate, days_for_self, email_addrs_and_days_for_others)


def update_pending_order(order, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    order.update(rate, days_for_self, email_addrs_and_days_for_others)


def process_stripe_charge(order, token):
    assert order.payment_required()
    try:
        charge = create_charge_for_order(order, token)
        confirm_order(order, charge.id)
    except stripe.error.CardError as e:
        mark_order_as_failed(order, e._message)


def confirm_order(order, charge_id):
    order.confirm(charge_id)
    send_receipt(order)
    send_ticket_invitations(order)


def mark_order_as_failed(order, charge_failure_reason):
    order.mark_as_failed(charge_failure_reason)


def send_receipt(order):
    # TODO
    pass


def send_ticket_invitations(order):
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket.invitation())


def claim_ticket_invitation(owner, invitation):
    invitation.claim_for_owner(owner)
