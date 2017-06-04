import stripe

from .invitation_mailer import send_invitation_mail
from .models import Order
from .stripe_integration import create_charge_for_order


def create_pending_order(purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    assert days_for_self or email_addrs_and_days_for_others

    unconfirmed_details = {
        'days_for_self': days_for_self,
        'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
    }

    return Order.objects.create(
        purchaser=purchaser,
        rate=rate,
        status='pending',
        unconfirmed_details=unconfirmed_details,
    )


def update_pending_order(order, rate, days_for_self=None, email_addrs_and_days_for_others=None):
    assert days_for_self is not None or email_addrs_and_days_for_others is not None
    assert order.payment_required()

    order.rate = rate
    order.unconfirmed_details = {
        'days_for_self': days_for_self,
        'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
    }
    order.save()


def confirm_order(order, charge_id):
    assert order.payment_required()

    days_for_self = order.unconfirmed_details['days_for_self']
    if days_for_self is not None:
        order.tickets.create_for_user(order.purchaser, days_for_self)

    email_addrs_and_days_for_others = order.unconfirmed_details['email_addrs_and_days_for_others']
    if email_addrs_and_days_for_others is not None:
        for email_addr, days in email_addrs_and_days_for_others:
            order.tickets.create_with_invitation(email_addr, days)

    order.stripe_charge_id = charge_id
    order.stripe_charge_failure_reason = ''
    order.status = 'successful'

    order.save()

    send_receipt(order)
    send_ticket_invitations(order)


def mark_order_as_failed(order, charge_failure_reason):
    order.stripe_charge_failure_reason = charge_failure_reason
    order.status = 'failed'

    order.save()


def process_stripe_charge(order, token):
    assert order.payment_required()
    try:
        charge = create_charge_for_order(order, token)
        confirm_order(order, charge.id)
    except stripe.error.CardError as e:
        mark_order_as_failed(order, e._message)


def send_receipt(order):
    # TODO
    pass


def send_ticket_invitations(order):
    for ticket in order.unclaimed_tickets():
        send_invitation_mail(ticket.invitation())


def claim_ticket_invitation(owner, invitation):
    invitation.claim_for_owner(owner)
