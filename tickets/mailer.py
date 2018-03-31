import re

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse

from ironcage.emails import send_mail
from tickets.models import Ticket


INVITATION_TEMPLATE = '''
Hello!

{purchaser_name} has purchased you a ticket for PyCon UK 2018.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2018 team
'''.strip()


FREE_TICKET_INVITATION_TEMPLATE = '''
Hello!

You have been assigned a ticket for PyCon UK 2018.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2018 team
'''.strip()


def send_invitation_mail(ticket):
    invitation = ticket.invitation
    url = settings.DOMAIN + invitation.get_absolute_url()
    if ticket.rate == Ticket.FREE:
        body = FREE_TICKET_INVITATION_TEMPLATE.format(url=url)
    else:
        purchaser_name = ticket.invoice.purchaser.name
        body = INVITATION_TEMPLATE.format(purchaser_name=purchaser_name, url=url)

    send_mail(
        f'PyCon UK 2018 ticket invitation ({ticket.ticket_id})',
        body,
        invitation.email_addr,
    )


def send_order_confirmation_mail(order):
    assert not order.payment_required

    template = get_template('tickets/emails/order-confirmation.txt')
    context = {
        'purchaser_name': order.purchaser.name,
        'num_tickets': len(order.tickets()),
        'tickets_for_others': [ticket for ticket in order.tickets() if ticket.owner != order.purchaser],
        'ticket_for_self': [ticket for ticket in order.tickets() if ticket.owner == order.purchaser],
        'receipt_url': settings.DOMAIN + reverse('payments:payment', args=[order.payments.all()[0].id]),
    }
    body_raw = template.render(context)
    body = re.sub('\n\n\n+', '\n\n', body_raw)

    send_mail(
        f'PyCon UK 2018 order confirmation ({order.item_id})',
        body,
        order.purchaser.email_addr,
    )


ORDER_REFUND_TEMPLATE = '''
Hi {purchaser_name},

Your order for PyCon UK 2018 has been refunded.

~ The PyCon UK 2018 team
'''.strip()


def send_order_refund_mail(order):
    body = ORDER_REFUND_TEMPLATE.format(purchaser_name=order.purchaser.name)

    send_mail(
        f'PyCon UK 2018 order refund ({order.item_id})',
        body,
        order.purchaser.email_addr,
    )
