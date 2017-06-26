from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .actions import claim_ticket_invitation, create_pending_order, process_stripe_charge, update_pending_order
from .forms import CompanyDetailsForm, TicketForm, TicketForSelfForm, TicketForOthersFormSet
from .models import Order, Ticket, TicketInvitation
from .prices import PRICES_INCL_VAT, cost_incl_vat


def new_order(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = TicketForm(request.POST)
        self_form = TicketForSelfForm(request.POST)
        others_formset = TicketForOthersFormSet(request.POST)
        company_details_form = CompanyDetailsForm(request.POST)

        if form.is_valid():
            who = form.cleaned_data['who']
            rate = form.cleaned_data['rate']

            if who == 'self':
                valid = self_form.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = None
            elif who == 'others':
                valid = others_formset.is_valid()
                if valid:
                    days_for_self = None
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            elif who == 'self and others':
                valid = self_form.is_valid() and others_formset.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            else:
                assert False

            if valid:
                if rate == 'corporate':
                    valid = company_details_form.is_valid()
                    if valid:
                        company_details = {
                            'name': company_details_form.cleaned_data['company_name'],
                            'addr': company_details_form.cleaned_data['company_addr'],
                        }
                else:
                    company_details = None

            if valid:
                order = create_pending_order(
                    purchaser=request.user,
                    rate=rate,
                    days_for_self=days_for_self,
                    email_addrs_and_days_for_others=email_addrs_and_days_for_others,
                    company_details=company_details,
                )

                return redirect(order)

    else:
        form = TicketForm()
        self_form = TicketForSelfForm()
        others_formset = TicketForOthersFormSet()
        company_details_form = CompanyDetailsForm()

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'company_details_form': company_details_form,
        'user_can_buy_for_self': request.user.is_authenticated() and not request.user.get_ticket(),
        'rates_table_data': _rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
    }

    return render(request, 'tickets/new_order.html', context)


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
        form = TicketForm(request.POST)
        self_form = TicketForSelfForm(request.POST)
        others_formset = TicketForOthersFormSet(request.POST)
        company_details_form = CompanyDetailsForm(request.POST)

        if form.is_valid():
            who = form.cleaned_data['who']
            rate = form.cleaned_data['rate']

            if who == 'self':
                valid = self_form.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = None
            elif who == 'others':
                valid = others_formset.is_valid()
                if valid:
                    days_for_self = None
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            elif who == 'self and others':
                valid = self_form.is_valid() and others_formset.is_valid()
                if valid:
                    days_for_self = self_form.cleaned_data['days']
                    email_addrs_and_days_for_others = others_formset.email_addrs_and_days
            else:
                assert False

            if valid:
                if rate == 'corporate':
                    valid = company_details_form.is_valid()
                    if valid:
                        company_details = {
                            'name': company_details_form.cleaned_data['company_name'],
                            'addr': company_details_form.cleaned_data['company_addr'],
                        }
                else:
                    company_details = None

            if valid:
                update_pending_order(
                    order,
                    rate=rate,
                    days_for_self=days_for_self,
                    email_addrs_and_days_for_others=email_addrs_and_days_for_others,
                    company_details=company_details,
                )

                return redirect(order)

    else:
        form = TicketForm(order.form_data())
        self_form = TicketForSelfForm(order.self_form_data())
        others_formset = TicketForOthersFormSet(order.others_formset_data())
        company_details_form = CompanyDetailsForm(order.company_details_form_data())

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'company_details_form': company_details_form,
        'user_can_buy_for_self': not request.user.get_ticket(),
        'rates_table_data': _rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
    }

    return render(request, 'tickets/order_edit.html', context)


@login_required
def order(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the order')
        return redirect('index')

    if order.payment_required():
        if request.user.get_ticket() is not None and order.unconfirmed_details['days_for_self']:
            messages.warning(request, 'You already have a ticket.  Please amend your order.')
            return redirect('tickets:order_edit', order.order_id)

    if order.status == 'failed':
        messages.error(request, f'Payment for this order failed ({order.stripe_charge_failure_reason})')
    elif order.status == 'errored':
        messages.error(request, 'There was an error creating your order.  You card may have been charged, but if so the charge will have been refunded.  Please make a new order.')

    ticket = request.user.get_ticket()
    if ticket is not None and ticket.order != order:
        ticket = None

    context = {
        'order': order,
        'ticket': ticket,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
        'show_sidebar': True,
    }
    return render(request, 'tickets/order.html', context)


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

    if request.user.get_ticket() is not None and order.unconfirmed_details['days_for_self']:
        messages.warning(request, 'You already have a ticket.  Please amend your order.  Your card has not been charged.')
        return redirect('tickets:order_edit', order.order_id)

    token = request.POST['stripeToken']
    process_stripe_charge(order, token)

    if not order.payment_required():
        messages.success(request, 'Payment for this order has been received.')

    return redirect(order)


@login_required
def order_receipt(request, order_id):
    order = Order.objects.get_by_order_id_or_404(order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the receipt')
        return redirect('index')

    if order.payment_required():
        messages.error(request, 'This order has not been paid')
        return redirect(order)

    context = {
        'order': order,
        'no_navbar': True,
    }
    return render(request, 'tickets/order_receipt.html', context)


@login_required
def ticket(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)

    if request.user != ticket.owner:
        messages.warning(request, 'Only the owner of a ticket can view the ticket')
        return redirect('index')

    if not request.user.profile_complete():
        messages.warning(request, 'Your profile is incomplete')

    context = {
        'ticket': ticket,
        'show_sidebar': True,
    }
    return render(request, 'tickets/ticket.html', context)


def ticket_invitation(request, token):
    invitation = get_object_or_404(TicketInvitation, token=token)

    if not request.user.is_authenticated:
        messages.info(request, 'You need to create an account to claim your invitation')
        return redirect(settings.LOGIN_URL)

    if request.user.get_ticket() is not None:
        messages.error(request, 'You already have a ticket!  Please contact pyconuk-enquiries@python.org to arrange transfer of this invitaiton to somebody else.')
        return redirect('index')

    ticket = invitation.ticket

    if invitation.status == 'unclaimed':
        assert ticket.owner is None
        claim_ticket_invitation(request.user, invitation)
    elif invitation.status == 'claimed':
        assert ticket.owner is not None
        messages.info(request, 'This invitation has already been claimed')
    else:
        assert False

    return redirect(ticket)


def _rates_data():
    return PRICES_INCL_VAT


def _rates_table_data():
    data = []
    data.append(['', 'Individual rate', 'Corporate rate'])
    for ix in range(5):
        num_days = ix + 1
        individual_rate = cost_incl_vat('individual', num_days)
        corporate_rate = cost_incl_vat('corporate', num_days)
        if num_days == 1:
            data.append(['1 day', f'£{individual_rate}', f'£{corporate_rate}'])
        else:
            data.append([f'{num_days} days', f'£{individual_rate}', f'£{corporate_rate}'])

    return data
