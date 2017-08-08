from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .actions import create_pending_order, process_stripe_charge, update_pending_order
from .forms import OrderForm, TicketFormSet
from .models import Order


def new_order(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        order_form = OrderForm(request.POST)
        ticket_formset = TicketFormSet(request.POST)

        if order_form.is_valid() and ticket_formset.is_valid():
            unconfirmed_details = []
            for form in ticket_formset.forms:
                name = form.cleaned_data['name']
                date_of_birth = form.cleaned_data['date_of_birth']
                if date_of_birth is not None:
                    date_of_birth = str(date_of_birth)
                unconfirmed_details.append([name, date_of_birth])

            order = create_pending_order(
                purchaser=request.user,
                adult_name=order_form.cleaned_data['adult_name'],
                adult_phone_number=order_form.cleaned_data['adult_phone_number'],
                adult_email_addr=order_form.cleaned_data['adult_email_addr'],
                accessibility_reqs=order_form.cleaned_data['accessibility_reqs'],
                dietary_reqs=order_form.cleaned_data['dietary_reqs'],
                unconfirmed_details=unconfirmed_details,
            )
            return redirect(order)

    else:
        order_form = OrderForm()
        ticket_formset = TicketFormSet()

    context = {
        'order_form': order_form,
        'ticket_formset': ticket_formset,
        'js_paths': ['children/order_form.js'],
    }

    return render(request, 'children/new_order.html', context)


@login_required
def order_edit(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        ticket_formset = TicketFormSet(request.POST)

        if order_form.is_valid() and ticket_formset.is_valid():
            unconfirmed_details = []
            for form in ticket_formset.forms:
                name = form.cleaned_data['name']
                date_of_birth = form.cleaned_data['date_of_birth']
                if date_of_birth is not None:
                    date_of_birth = str(date_of_birth)
                unconfirmed_details.append([name, date_of_birth])

            update_pending_order(
                order,
                adult_name=order_form.cleaned_data['adult_name'],
                adult_phone_number=order_form.cleaned_data['adult_phone_number'],
                adult_email_addr=order_form.cleaned_data['adult_email_addr'],
                accessibility_reqs=order_form.cleaned_data['accessibility_reqs'],
                dietary_reqs=order_form.cleaned_data['dietary_reqs'],
                unconfirmed_details=unconfirmed_details,
            )
            return redirect(order)
    else:
        order_form = OrderForm(instance=order)
        formset_data = {
            'form-TOTAL_FORMS': str(len(order.unconfirmed_details)),
            'form-INITIAL_FORMS': str(len(order.unconfirmed_details)),
        }
        for ix, (name, date_of_birth) in enumerate(order.unconfirmed_details):
            formset_data[f'form-{ix}-name'] = name
            formset_data[f'form-{ix}-date_of_birth'] = date_of_birth

        ticket_formset = TicketFormSet(formset_data)

    context = {
        'order_form': order_form,
        'ticket_formset': ticket_formset,
        'js_paths': ['children/order_form.js'],
    }

    return render(request, 'children/order_edit.html', context)


@login_required
def order(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the order')
        return redirect('index')

    if order.status == 'failed':
        messages.error(request, f'Payment for this order failed ({order.stripe_charge_failure_reason})')

    context = {
        'order': order,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }
    return render(request, 'children/order.html', context)


@login_required
@require_POST
def order_payment(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can pay for the order')
        return redirect('index')

    if not order.payment_required():
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    token = request.POST['stripeToken']
    process_stripe_charge(order, token)

    if not order.payment_required():
        messages.success(request, 'Payment for this order has been received.')

    return redirect(order)
