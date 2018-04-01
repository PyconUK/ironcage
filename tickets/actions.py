# The functions defined in this module should be the only way that Orders,
# Tickets, and TicketInvitations are created or updated by the rest of the
# code.  This has at least two benefits:
#
#  * It makes it easier to see how and when data is changed.
#  * The only way that data can be set up for testing is through calling
#    functions in this module.  This means that test data should always be
#    in a consistent state.


from django.db import transaction

from payments.stripe_integration import refund_charge

from .mailer import send_invitation_mail, send_order_refund_mail
from .models import Ticket
from payments import actions as payment_actions

import structlog
logger = structlog.get_logger()


def create_ticket(purchaser, rate, days=None):
    logger.info('create_ticket', purchaser=purchaser.id, rate=rate, days=days)
    with transaction.atomic():
        return Ticket.objects.create_for_user(
            purchaser,
            rate,
            days,
        )


def create_ticket_with_invitation(email, rate, days=None):
    logger.info('create_ticket_with_invitation', email=email, rate=rate, days=days)
    with transaction.atomic():
        return Ticket.objects.create_with_invitation(
            email,
            rate,
            days,
        )


def create_invoice_with_tickets(user, rate, days_for_self, email_addrs_and_days_for_others,
                                company_details):
    logger.info('create_invoice_with_tickets', purchaser=user.id, rate=rate)

    company_name = company_details['name'] if isinstance(company_details, dict) else None
    company_addr = company_details['addr'] if isinstance(company_details, dict) else None

    invoice = payment_actions.create_new_invoice(user, company_name, company_addr)

    if days_for_self:
        ticket = create_ticket(user, rate, days_for_self)
        invoice.add_item(ticket)

    if email_addrs_and_days_for_others is not None:
        for email_addr, days in email_addrs_and_days_for_others:
            ticket = create_ticket_with_invitation(email_addr, rate, days)
            invoice.add_item(ticket)

    return invoice



def create_unpaid_order(purchaser, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    return create_invoice_with_tickets(purchaser, rate, days_for_self, email_addrs_and_days_for_others, company_details)
    # logger.info('create_unpaid_order', purchaser=purchaser.id, rate=rate)
    # with transaction.atomic():
    #     return Order.objects.create_pending(
    #         purchaser,
    #         rate,
    #         days_for_self,
    #         email_addrs_and_days_for_others,
    #         company_details=company_details,
    #     )


def update_unpaid_order(order, rate, days_for_self=None, email_addrs_and_days_for_others=None, company_details=None):
    logger.info('update_unpaid_order', order=order.id, rate=rate)
    with transaction.atomic():
        order.update(rate, days_for_self, email_addrs_and_days_for_others, company_details)


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
