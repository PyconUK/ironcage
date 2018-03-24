from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from payments import actions as payment_actions
from payments.models import Invoice
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
def invoice(request, invoice_id):
    pass
    # order = get_object_or_404(Invoice, invoice_id)

    # # if request.user != order.purchaser:
    # #     messages.warning(request, 'Only the purchaser of an order can view the receipt')
    # #     return redirect('index')

    # # if order.payment_required():
    # #     messages.error(request, 'This order has not been paid')
    # #     return redirect(order)

    # context = {
    #     'order': order,
    #     'title': f'PyCon UK 2018 invoice {order.order_id}',
    #     'no_navbar': True,
    # }
    # return render(request, 'tickets/order_receipt.html', context)
