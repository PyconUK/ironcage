from django.conf import settings
from django.core.mail import send_mail


INVITATION_TEMPLATE = '''
Hello!

{purchaser_name} has purchased you a ticket for PyCon UK 2017.

Please click here to claim your ticket:

    {url}

We look forward to seeing you in Cardiff!

~ The PyCon UK 2017 team
'''.strip()


def send_invitation_mail(invitation):
    ticket = invitation.ticket
    purchaser_name = ticket.order.purchaser.username  # TODO get name from profile
    url = settings.DOMAIN + invitation.get_absolute_url()
    body = INVITATION_TEMPLATE.format(purchaser_name=purchaser_name, url=url)

    send_mail(
        f'PyCon UK 2017 ticket invitation ({ticket.ticket_id})',
        body,
        'PyCon UK 2017 <tickets@pyconuk.org>',  # TODO either set up this address, or find another one to use
        [invitation.email_addr],
        fail_silently=False,
    )
