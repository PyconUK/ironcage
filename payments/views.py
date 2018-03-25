from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from payments import actions as payment_actions
from payments.models import Invoice, Payment
from tickets import actions
from tickets.forms import CompanyDetailsForm, TicketForm, TicketForSelfForm, TicketForOthersFormSet
from tickets.models import Ticket, TicketInvitation
from tickets.prices import PRICES_INCL_VAT, cost_incl_vat


@login_required
def order(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.user != invoice.purchaser:
        messages.warning(request, 'Only the purchaser of an invoice can view the invoice')
        return redirect('index')

    # if invoice.payment_required():
    #     if request.user.get_ticket() is not None and invoice.unconfirmed_details['days_for_self']:
    #         messages.warning(request, 'You already have a ticket.  Please amend your invoice.')
    #         return redirect('tickets:order_edit', invoice.invoice_id)

    # if invoice.status == 'failed':
    #     messages.error(request, f'Payment for this invoice failed ({invoice.stripe_charge_failure_reason})')
    # elif invoice.status == 'errored':
    #     messages.error(request, 'There was an error creating your invoice.  You card may have been charged, but if so the charge will have been refunded.  Please make a new invoice.')

    # ticket = request.user.get_ticket()
    # if ticket is not None and ticket.invoice != invoice:
    #     ticket = None

    context = {
        'invoice': invoice,
        # 'ticket': ticket,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }
    return render(request, 'payments/order.html', context)


@login_required
def order_edit(request, order_id):
    order = get_object_or_404(Invoice, pk=order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can update the order')
        return redirect('index')

    if not order.payment_required:
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
                actions.update_pending_order(
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
@require_POST
def invoice_payment(request, order_id):
    order = get_object_or_404(Invoice, pk=order_id)

    if request.user != order.purchaser:
        messages.warning(request, 'Only the purchaser of an order can pay for the order')
        return redirect('index')

    if not order.payment_required:
        messages.error(request, 'This order has already been paid')
        return redirect(order)

    # if request.user.get_ticket() is not None and order.unconfirmed_details['days_for_self']:
    #     messages.warning(request, 'You already have a ticket.  Please amend your order.  Your card has not been charged.')
    #     return redirect('tickets:order_edit', order.order_id)

    token = request.POST['stripeToken']
    payment_actions.process_stripe_charge(order, token)

    if not order.payment_required:
        messages.success(request, 'Payment for this order has been received.')

    return redirect(order)


@login_required
def payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)

    if request.user != payment.invoice.purchaser:
        messages.warning(request, 'Only the purchaser of an order can view the receipt')
        return redirect('index')

    context = {
        'payment': payment,
        'invoice': payment.invoice,
        'title': f'PyCon UK 2018 Receipt {payment.id}',
        'no_navbar': True,
    }
    return render(request, 'payments/payment_receipt.html', context)



