import re

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse

from ironcage.emails import send_mail


def send_order_confirmation_mail(order):
    assert not order.payment_required()

    template = get_template('children/emails/order-confirmation.txt')
    context = {
        'purchaser_name': order.purchaser.name,
        'num_tickets': order.num_tickets(),
        'order_url': settings.DOMAIN + reverse('children:order', args=[order.order_id]),
    }
    body_raw = template.render(context)
    body = re.sub('\n\n\n+', '\n\n', body_raw)

    send_mail(
        f"PyCon UK 2018 children's day order confirmation ({order.order_id})",
        body,
        order.purchaser.email_addr,
    )
