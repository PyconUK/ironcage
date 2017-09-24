import re

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse

from ironcage.emails import send_mail


INVITATION_TEMPLATE = '''
Hello!

{purchaser_name} has purchased you a ticket for PyCon UK 2017.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2017 team
'''.strip()


FREE_TICKET_INVITATION_TEMPLATE = '''
Hello!

You have been assigned a ticket for PyCon UK 2017.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2017 team
'''.strip()


def send_invitation_mail(ticket):
    invitation = ticket.invitation()
    url = settings.DOMAIN + invitation.get_absolute_url()
    if ticket.order is None:
        body = FREE_TICKET_INVITATION_TEMPLATE.format(url=url)
    else:
        purchaser_name = ticket.order.purchaser.name
        body = INVITATION_TEMPLATE.format(purchaser_name=purchaser_name, url=url)

    send_mail(
        f'PyCon UK 2017 ticket invitation ({ticket.ticket_id})',
        body,
        invitation.email_addr,
    )


def send_order_confirmation_mail(order):
    assert not order.payment_required()

    template = get_template('tickets/emails/order-confirmation.txt')
    context = {
        'purchaser_name': order.purchaser.name,
        'num_tickets': order.num_tickets(),
        'tickets_for_others': order.tickets_for_others(),
        'ticket_for_self': order.ticket_for_self(),
        'receipt_url': settings.DOMAIN + reverse('tickets:order_receipt', args=[order.order_id]),
    }
    body_raw = template.render(context)
    body = re.sub('\n\n\n+', '\n\n', body_raw)

    send_mail(
        f'PyCon UK 2017 order confirmation ({order.order_id})',
        body,
        order.purchaser.email_addr,
    )


ORDER_REFUND_TEMPLATE = '''
Hi {purchaser_name},

Your order for PyCon UK 2017 has been refunded.

~ The PyCon UK 2017 team
'''.strip()


def send_order_refund_mail(order):
    body = ORDER_REFUND_TEMPLATE.format(purchaser_name=order.purchaser.name)

    send_mail(
        f'PyCon UK 2017 order refund ({order.order_id})',
        body,
        order.purchaser.email_addr,
    )
