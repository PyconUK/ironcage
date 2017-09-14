from collections import namedtuple

from django.conf import settings
from django.db import models


class Booking(models.Model):
    guest = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    room_key = models.CharField(max_length=100)

    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_created = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Manager(models.Manager):
        def for_room(self, room_key):
            return self.filter(room_key=room_key)

    objects = Manager()

    def get_room(self):
        return get_room_by_key(self.room_key)

    def room_description(self):
        return self.get_room().description


Room = namedtuple('Room', ['key', 'description', 'capacity', 'cost_incl_vat'])

ROOMS = [
    Room('mrs-potts-women', "Bed in women's dorm at Mrs Potts, breakfast included", 15, 130),
    Room('mrs-potts-men', "Bed in men's dorm at Mrs Potts, breakfast included", 15, 130),
    Room('mrs-potts-mixed', 'Bed in mixed dorm at Mrs Potts, breakfast included', 15, 130),
    Room('bunkhouse-mixed', "Bed in mixed dorm at Bunkhouse Cardif", 20, 98),
]


def get_room_by_key(key):
    for room in ROOMS:
        if room.key == key:
            return room
    raise KeyError


def has_availability(room):
    num_taken = Booking.objects.for_room(room.key).count()
    num_available = room.capacity - num_taken

    # This might happen if two people booked the last room at exactly the same time
    assert num_available >= 0, f'There are negative beds available in {room}'

    return (num_available > 0)


def available_rooms():
    return [room for room in ROOMS if has_availability(room)]
