import re

from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse

from ironcage.emails import send_mail


def send_booking_confirmation_mail(booking):
    user = booking.guest
    subject = f'PyCon UK 2017 dinner confirmation | {user.user_id}'

    template = get_template('dinners/emails/order-confirmation.txt')
    context = {
        'booking': booking,
        'receipt_url': settings.DOMAIN + reverse('dinners:conference_dinner_receipt'),
    }
    body_raw = template.render(context)
    body = re.sub('\n\n\n+', '\n\n', body_raw)

    send_mail(
        subject,
        body,
        booking.guest.email_addr,
    )
