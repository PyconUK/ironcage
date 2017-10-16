from accounts.tests.factories import create_user

from dinners.models import Booking
from dinners.menus import MENUS


def create_contributors_booking(user=None, venue='contributors'):
    if user is None:
        user = create_user()

    menu = MENUS[venue]

    return Booking.objects.create(
        guest=user,
        venue=venue,
        starter=menu['starter'][0][0],
        main=menu['main'][0][0],
        pudding=menu['pudding'][0][0],
    )


def create_paid_booking(user=None):
    if user is None:
        user = create_user()

    venue = 'conference'
    menu = MENUS[venue]

    return Booking.objects.create(
        guest=user,
        venue=venue,
        starter=menu['starter'][0][0],
        main=menu['main'][0][0],
        pudding=menu['pudding'][0][0],
    )


def create_all_bookings(venue):
    for _ in range(MENUS[venue]['capacity']):
        create_contributors_booking(venue=venue)
