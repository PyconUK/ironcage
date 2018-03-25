# The functions defined in this module should be the only way that Orders,
# Tickets, and TicketInvitations are created or updated by the rest of the
# code.  This has at least two benefits:
#
#  * It makes it easier to see how and when data is changed.
#  * The only way that data can be set up for testing is through calling
#    functions in this module.  This means that test data should always be
#    in a consistent state.

from django_slack import slack_message
import stripe

from django.db import transaction
from django.db.utils import IntegrityError

from ironcage.stripe_integration import create_charge_for_order, refund_charge

from .mailer import send_invitation_mail, send_order_confirmation_mail, send_order_refund_mail
from .models import Order, Ticket

import structlog
logger = structlog.get_logger()


def create_pending_order(purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    logger.info('create_pending_order', purchaser=purchaser.id, rate=rate)
    with transaction.atomic():
        return Order.objects.create_pending(
            purchaser,
            rate,
            days_for_self,
            email_addrs_and_days_for_others,
            company_details=company_details,
        )


def update_pending_order(order, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    logger.info('update_pending_order', order=order.order_id, rate=rate)
    with transaction.atomic():
        order.update(rate, days_for_self, email_addrs_and_days_for_others, company_details)


# def process_stripe_charge(order, token):
#     logger.info('process_stripe_charge', order=order.order_id, token=token)
#     assert order.payment_required()
#     try:
#         charge = create_charge_for_order(order, token)
#         confirm_order(order, charge.id, charge.created)
#     except stripe.error.CardError as e:
#         mark_order_as_failed(order, e._message)
#     except IntegrityError:
#         refund_charge(charge.id)
#         mark_order_as_errored_after_charge(order, charge.id)


# def confirm_order(order, charge_id, charge_created):
#     logger.info('confirm_order', order=order.order_id, charge_id=charge_id)
#     with transaction.atomic():
#         order.confirm(charge_id, charge_created)
#     send_receipt(order)
#     send_ticket_invitations(order)
#     slack_message('tickets/order_created.slack', {'order': order})


def mark_order_as_failed(order, charge_failure_reason):
    logger.info('mark_order_as_failed', order=order.order_id, charge_failure_reason=charge_failure_reason)
    with transaction.atomic():
        order.mark_as_failed(charge_failure_reason)


def mark_order_as_errored_after_charge(order, charge_id):
    logger.warn('mark_order_as_errored_after_charge', order=order.order_id, charge_id=charge_id)
    with transaction.atomic():
        order.march_as_errored_after_charge(charge_id)


def create_free_ticket(email_addr, pot):
    logger.info('create_free_ticket', email_addr=email_addr, pot=pot)
    with transaction.atomic():
        ticket = Ticket.objects.create_free_with_invitation(
            email_addr=email_addr,
            pot=pot,
        )
    send_invitation_mail(ticket)
    return ticket


def update_free_ticket(ticket, days):
    logger.info('update_free_ticket', ticket=ticket.ticket_id, days=days)
    with transaction.atomic():
        ticket.update_days(days)


# def send_receipt(order):
#     logger.info('send_receipt', order=order.order_id)
#     send_order_confirmation_mail(order)


# def send_ticket_invitations(order):
#     logger.info('send_ticket_invitations', order=order.order_id)
#     for ticket in order.unclaimed_tickets():
#         send_invitation_mail(ticket)


def claim_ticket_invitation(owner, invitation):
    logger.info('claim_ticket_invitation', owner=owner.id, invitation=invitation.token)
    with transaction.atomic():
        invitation.claim_for_owner(owner)


def reassign_ticket(ticket, email_addr):
    logger.info('reassign_ticket', ticket=ticket.ticket_id, email_addr=email_addr)
    with transaction.atomic():
        ticket.reassign(email_addr)
    send_invitation_mail(ticket)


def refund_order(order):
    logger.info('refund_order', order=order.order_id)
    assert order.status == 'successful'
    with transaction.atomic():
        order.delete_tickets_and_mark_as_refunded()
    refund_charge(order.stripe_charge_id)
    send_order_refund_mail(order)
