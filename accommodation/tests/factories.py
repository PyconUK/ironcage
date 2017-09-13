from datetime import datetime, timezone

from accounts.tests.factories import create_user

from accommodation.models import Booking, ROOMS


def create_booking(user=None, room_key=None):
    if user is None:
        user = create_user()

    if room_key is None:
        room_key = ROOMS[0].key

    return Booking.objects.create(
        guest=user,
        room_key=room_key,
        stripe_charge_id='ch_abcdefghijklmnopqurstuvw',
        stripe_charge_created=datetime.fromtimestamp(1495355163, tz=timezone.utc),
    )


def create_all_bookings():
    for room in ROOMS:
        for _ in range(room.capacity):
            create_booking(room_key=room.key)


def create_some_bookings():
    for room in ROOMS[1:]:
        for _ in range(room.capacity):
            create_booking(room_key=room.key)
