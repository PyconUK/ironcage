from django.conf import settings
from django.db import models

from .menus import MENUS


class Booking(models.Model):
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='dinner_bookings', null=True, on_delete=models.CASCADE)
    venue = models.CharField(max_length=20)
    starter = models.CharField(max_length=100, null=True, blank=True)
    main = models.CharField(max_length=100, null=True, blank=True)
    pudding = models.CharField(max_length=100, null=True, blank=True)

    stripe_charge_id = models.CharField(max_length=80, null=True)
    stripe_charge_created = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def dinner_description(self):
        return MENUS[self.venue]['description']

    def starter_descr(self):
        return dict(MENUS[self.venue]['starter'])[self.starter]

    def main_descr(self):
        return dict(MENUS[self.venue]['main'])[self.main]

    def pudding_descr(self):
        return dict(MENUS[self.venue]['pudding'])[self.pudding]

    def paid_booking(self):
        return bool(self.stripe_charge_id)


def seats_left(venue):
    num_taken = Booking.objects.filter(venue=venue).count()
    num_available = MENUS[venue]['capacity'] - num_taken

    # This might happen if two people booked the last seat at exactly the same time
    assert num_available >= 0, f'There are negative seats available in {venue}'

    return (num_available > 0)
