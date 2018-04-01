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

    # TODO
    # if not invoice.successful_payment:
    #     if request.user.get_ticket() is not None and invoice.unconfirmed_details['days_for_self']:
    #         messages.warning(request, 'You already have a ticket.  Please amend your invoice.')
    #         return redirect('tickets:order_edit', invoice.invoice_id)

    if invoice.payment_status == Payment.FAILED:
        messages.error(request, f'Payment for this invoice failed')
    elif invoice.payment_status == Payment.ERRORED:
        messages.error(request, 'There was an error creating your invoice. Your card may have been charged, but if so the charge will have been refunded.  Please make a new invoice.')

    ticket = request.user.get_ticket()
    if ticket is not None and ticket.invoice != invoice:
        ticket = None

    context = {
        'invoice': invoice,
        'ticket': ticket,
        'stripe_api_key': settings.STRIPE_API_KEY_PUBLISHABLE,
    }
    return render(request, 'payments/order.html', context)


@login_required
@require_POST
def invoice_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.user != invoice.purchaser:
        messages.warning(request, 'Only the purchaser of an invoice can pay for the invoice')
        return redirect('index')

    if invoice.successful_payment:
        messages.error(request, 'This invoice has already been paid')
        return redirect(invoice)

    # if request.user.get_ticket() is not None and invoice.unconfirmed_details['days_for_self']:
    #     messages.warning(request, 'You already have a ticket.  Please amend your invoice.  Your card has not been charged.')
    #     return redirect('tickets:order_edit', invoice.invoice_id)

    token = request.POST['stripeToken']
    payment = payment_actions.pay_invoice_by_stripe(invoice, token)

    if not invoice.payment_required and payment.status == Payment.SUCCESSFUL:
        messages.success(request, 'Payment for this invoice has been received.')
    else:
        messages.error(request, f'There was an error with your payment: {payment.charge_failure_reason}')

    return redirect(invoice)


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



