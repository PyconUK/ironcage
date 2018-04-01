from datetime import datetime, timezone

from django_slack import slack_message
import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from payments.stripe_integration import create_charge

from .mailer import send_booking_confirmation_mail
from .models import Booking, available_rooms, get_room_by_key, has_availability


def new_booking(request):
    if request.user.is_authenticated and request.user.get_accommodation_booking():
        messages.warning(request, 'You have already booked a room')
        return redirect('index')

    context = {
        'rooms': available_rooms(),
    }

    return render(request, 'accommodation/new_booking.html', context)


@login_required
def booking_payment(request):
    if request.user.get_accommodation_booking():
        messages.warning(request, 'You have already booked a room')
        return redirect('index')

    key = request.GET.get('room')

    try:
        room = get_room_by_key(key)
    except KeyError:
        messages.warning(request, 'That room does not exist')
        return redirect('index')

    if not has_availability(room):
        messages.warning(request, f'{room.description} is sold out')
        return redirect('accommodation:new_booking')

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            charge = create_charge(
                room.cost_incl_vat * 100,
                'PyCon UK 2018 accommodation',
                'PyCon UK accommodation',
                token
            )
        except stripe.error.CardError as e:
            messages.warning(request, f'Payment for this booking failed ({e._message})')
            return redirect('accommodation:new_booking')

        booking = Booking.objects.create(
            guest=request.user,
            room_key=room.key,
            stripe_charge_id=charge.id,
            stripe_charge_created=datetime.fromtimestamp(charge.created, tz=timezone.utc),
        )

        send_booking_confirmation_mail(booking)
        slack_message('accommodation/booking_created.slack', {'booking': booking})
        messages.info(request, 'Payment for this booking has been received')
        return redirect('index')

    context = {
        'room': room,
        'amount_pence': room.cost_incl_vat * 100,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }

    return render(request, 'accommodation/booking_payment.html', context)


@login_required
def booking_receipt(request):
    booking = request.user.get_accommodation_booking()
    if not booking:
        messages.warning(request, "You haven't booked accommodation")
        return redirect('index')

    context = {
        'booking': booking,
        'no_navbar': True,
    }

    return render(request, 'accommodation/booking_receipt.html', context)
