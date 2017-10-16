from datetime import datetime, timezone

import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from ironcage.stripe_integration import create_charge

from .forms import ConferenceDinnerForm, ContributorsDinnerForm, WhichDinnerForm
from .models import Booking, seats_left


CONFERENCE_DINNER_PRICE_POUNDS = 30
CONFERENCE_DINNER_PRICE_PENCE = CONFERENCE_DINNER_PRICE_POUNDS * 100


@login_required
def contributors_dinner(request):
    user = request.user
    if not user.is_contributor:
        messages.warning(request, "Only contributors are invited to the contributors' dinner")
        return redirect('index')

    booking = user.get_free_dinner_booking()
    if booking is None:
        return _contributors_dinner_unbooked(request)
    else:
        return _contributors_dinner_booked(request, booking)


def _contributors_dinner_booked(request, booking):
    if request.method == 'POST':
        messages.info(request, "You've already confirmed your place at the contributors' dinner")
        return redirect('dinners:contributors_dinner')

    context = {
        'booking': booking,
    }
    return render(request, 'dinners/contributors_dinner_booked.html', context)


def _contributors_dinner_unbooked(request):
    if request.method == 'POST':
        form = WhichDinnerForm(request.POST)
        if form.is_valid():
            which_dinner = form.cleaned_data['which_dinner']

            if not seats_left(which_dinner):
                messages.warning(request, 'Sorry, there are now no seats left for that dinner')
                return redirect('dinners:contributors_dinner')

            if which_dinner == 'contributors':
                menu_form = ContributorsDinnerForm(request.POST)
            elif which_dinner == 'conference':
                menu_form = ConferenceDinnerForm(request.POST)
            else:
                assert False

            if menu_form.is_valid():
                Booking.objects.create(
                    guest=request.user,
                    venue=which_dinner,
                    starter=menu_form.cleaned_data['starter'],
                    main=menu_form.cleaned_data['main'],
                    pudding=menu_form.cleaned_data['pudding'],
                )
                return redirect('dinners:contributors_dinner')

    context = {
        'which_dinner_form': WhichDinnerForm(),
        'contributors_dinner_form': ContributorsDinnerForm(),
        'conference_dinner_form': ConferenceDinnerForm(),
        'contributors_dinner_seats_left': seats_left('contributors'),
        'conference_dinner_seats_left': seats_left('conference'),
        'js_paths': ['dinners/contributors_form.js'],
    }
    return render(request, 'dinners/contributors_dinner_unbooked.html', context)


@login_required
def conference_dinner(request):
    user = request.user
    if user.is_contributor:
        booking = user.get_free_dinner_booking()
        if booking is None:
            return redirect('dinners:contributors_dinner')

    booking = user.get_conference_dinner_booking()

    if booking is None:
        context = {
            'seats_left': seats_left('conference'),
            'form': ConferenceDinnerForm(),
            'amount_pounds': CONFERENCE_DINNER_PRICE_POUNDS,
        }
        return render(request, 'dinners/conference_dinner_unbooked.html', context)
    else:
        context = {'booking': booking}
        return render(request, 'dinners/conference_dinner_booked.html', context)


@login_required
def conference_dinner_payment(request):
    if request.user.get_conference_dinner_booking():
        messages.warning(request, 'You have already booked for the conference dinner')
        return redirect('dinners:conference_dinner')

    if not seats_left('conference'):
        messages.warning(request, 'Sorry, there are now no seats left for the conference dinner')
        return redirect('dinners:conference_dinner')

    form = ConferenceDinnerForm(request.GET)
    if not form.is_valid():
        return redirect('dinners:conference_dinner')

    booking = Booking(
        guest=request.user,
        venue='conference',
        starter=form.cleaned_data['starter'],
        main=form.cleaned_data['main'],
        pudding=form.cleaned_data['pudding'],
    )

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            charge = create_charge(
                CONFERENCE_DINNER_PRICE_PENCE,
                'PyCon UK 2017 dinner',
                'PyCon UK dinner',
                token
            )
        except stripe.error.CardError as e:
            messages.warning(request, f'Payment failed ({e._message})')
            return redirect('dinners:conference_dinner')

        booking.stripe_charge_id = charge.id,
        booking.stripe_charge_created = datetime.fromtimestamp(charge.created, tz=timezone.utc)
        booking.save()

        messages.info(request, 'Payment succeeded')
        return redirect('dinners:conference_dinner')

    context = {
        'booking': booking,
        'amount_pounds': CONFERENCE_DINNER_PRICE_POUNDS,
        'amount_pence': CONFERENCE_DINNER_PRICE_PENCE,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }

    return render(request, 'dinners/conference_dinner_payment.html', context)
