from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .actions import claim_ticket_invitation, place_order_for_self, place_order_for_others, place_order_for_self_and_others, process_stripe_charge
from .constants import RATES
from .forms import TicketForm, TicketForSelfForm, TicketForOthersFormSet
from .models import Order, Ticket, TicketInvitation


@login_required
def new_order(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        self_form = TicketForSelfForm(request.POST)
        others_formset = TicketForOthersFormSet(request.POST)

        if form.is_valid():
            if form.cleaned_data['who'] == 'self':
                if self_form.is_valid():
                    order = place_order_for_self(
                        request.user,
                        form.cleaned_data['rate'],
                        self_form.cleaned_data['days'],
                    )

                    return redirect(order)

            elif form.cleaned_data['who'] == 'others':
                if others_formset.is_valid():
                    order = place_order_for_others(
                        request.user,
                        form.cleaned_data['rate'],
                        others_formset.email_addrs_and_days,
                    )

                    return redirect(order)

            elif form.cleaned_data['who'] == 'self and others':
                if self_form.is_valid() and others_formset.is_valid():
                    order = place_order_for_self_and_others(
                        request.user,
                        form.cleaned_data['rate'],
                        self_form.cleaned_data['days'],
                        others_formset.email_addrs_and_days,
                    )

                    return redirect(order)

            else:
                assert False

    else:
        form = TicketForm()
        self_form = TicketForSelfForm()
        others_formset = TicketForOthersFormSet()

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'rates_table_data': _rates_table_data(),
    }

    return render(request, 'tickets/new_order.html', context)


@login_required
def order(request, order_id):
    # TODO Only show to purchaser
    order = Order.objects.get_by_order_id_or_404(order_id)
    context = {
        'order': order,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }
    return render(request, 'tickets/order.html', context)


@login_required
@require_POST
def order_payment(request, order_id):
    # TODO Only show to purchaser
    order = Order.objects.get_by_order_id_or_404(order_id)
    token = request.POST['stripeToken']
    process_stripe_charge(order, token)
    return redirect(order)


@login_required
def ticket(request, ticket_id):
    # TODO Only show to owner
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)
    context = {
        'ticket': ticket,
    }
    return render(request, 'tickets/ticket.html', context)


@login_required
def ticket_invitation(request, token):
    invitation = get_object_or_404(TicketInvitation, token=token)
    ticket = invitation.ticket

    if invitation.status == 'unclaimed':
        assert ticket.owner is None
        claim_ticket_invitation(request.user, invitation)
        # message = None
    elif invitation.status == 'claimed':
        assert ticket.owner is not None
        # TODO Show message to user (#43)
        # message = 'This invitation has already been claimed'
    else:
        assert False

    return redirect(ticket)


def _rates_table_data():
    data = []
    data.append(['', 'Individual rate', 'Corporate rate'])
    for ix in range(5):
        num_days = ix + 1
        individual_rate = RATES['individual']['ticket_price'] + RATES['individual']['day_price'] * num_days
        corporate_rate = RATES['corporate']['ticket_price'] + RATES['corporate']['day_price'] * num_days
        if num_days == 1:
            data.append(['1 day', f'£{individual_rate}', f'£{corporate_rate}'])
        else:
            data.append([f'{num_days} days', f'£{individual_rate}', f'£{corporate_rate}'])

    return data
