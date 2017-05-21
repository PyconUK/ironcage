from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .actions import place_order_for_self, place_order_for_others, place_order_for_self_and_others
from .forms import TicketForm, TicketForSelfForm, TicketForOthersFormSet
from .models import Order, Ticket


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
    }

    return render(request, 'tickets/new_order.html', context)


@login_required
def order(request, order_id):
    # TODO Only show to purchaser
    order = Order.objects.get_by_order_id_or_404(order_id)
    context = {
        'order': order,
    }
    return render(request, 'tickets/order.html', context)


@login_required
def ticket(request, ticket_id):
    # TODO Only show to owner
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)
    context = {
        'ticket': ticket,
    }
    return render(request, 'tickets/ticket.html', context)
