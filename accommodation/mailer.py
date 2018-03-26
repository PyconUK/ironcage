from ironcage.emails import send_mail


INVITATION_TEMPLATE = '''
Hello!

You are booked for four nights, from Thursday 26th to Sunday 29th October, at:

    {room_description}

You can check in from 5pm.  When you check in, you will need to bring
photographic ID and a £5 key deposit.

We look forward to seeing you in Cardiff!

~ The PyCon UK 2018 team
'''.strip()


def send_booking_confirmation_mail(booking):
    body = INVITATION_TEMPLATE.format(room_description=booking.room_description())

    send_mail(
        f'PyCon UK 2018 accommodation confirmation',
        body,
        booking.guest.email_addr,
    )
