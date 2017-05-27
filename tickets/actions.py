from .invitation_mailer import send_invitation_mail
from .models import Order
from .stripe_integration import create_charge_for_order


def place_order_for_self(purchaser, rate, days):
    return Order.objects.create_with_ticket_for_purchaser(purchaser, rate, days)


def place_order_for_others(purchaser, rate, email_addrs_and_days):
    return Order.objects.create_with_tickets_for_others(purchaser, rate, email_addrs_and_days)


def place_order_for_self_and_others(purchaser, rate, self_days, email_addrs_and_days):
    return Order.objects.create_with_tickets_for_purchaser_and_others(purchaser, rate, self_days, email_addrs_and_days)


def process_stripe_charge(order, token):
    create_charge_for_order(order, token)
    if not order.payment_required():
        send_receipt(order)
        send_ticket_invitations(order)


def send_receipt(order):
    # TODO
    pass


def send_ticket_invitations(order):
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket.invitation())


def claim_ticket_invitation(owner, invitation):
    invitation.claim_for_owner(owner)
