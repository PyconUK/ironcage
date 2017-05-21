from .models import Order, Ticket


def place_order_for_self(purchaser, rate, days):
    return Order.objects.create_with_ticket_for_purchaser(purchaser, rate, days)


def place_order_for_others(purchaser, rate, email_addrs_and_days):
    return Order.objects.create_with_tickets_for_others(purchaser, rate, email_addrs_and_days)


def place_order_for_self_and_others(purchaser, rate, self_days, email_addrs_and_days):
    return Order.objects.create_with_tickets_for_purchaser_and_others(purchaser, rate, self_days, email_addrs_and_days)


def claim_ticket_invitation(owner, invitation):
    invitation.claim_for_owner(owner)
