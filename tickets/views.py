from decimal import Decimal

from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe

from payments import actions as payment_actions
from . import actions
from .forms import CompanyDetailsForm, TicketForm, TicketForSelfForm, TicketForOthersFormSet
from .models import Ticket, TicketInvitation
from .prices import PRICES_INCL_VAT, cost_incl_vat
from .constants import DAYS


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
                if rate == Ticket.CORPORATE:
                    valid = company_details_form.is_valid()
                    if valid:
                        company_details = {
                            'name': company_details_form.cleaned_data['company_name'],
                            'addr': company_details_form.cleaned_data['company_addr'],
                        }
                else:
                    company_details = None

            if valid:

                request.session['ticket_details'] = {
                    'rate': rate,
                    'days_for_self': days_for_self,
                    'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
                    'company_details': company_details,
                    'form': form.data,
                    'self_form': self_form.data,
                    'others_formset': others_formset.data,
                    'company_details_form': company_details_form.data,
                }

                return redirect('tickets:order_confirm')

    else:
        if datetime.now(timezone.utc) > settings.TICKET_SALES_CLOSE_AT:
            if request.GET.get('deadline-bypass-token', '') != settings.TICKET_DEADLINE_BYPASS_TOKEN:
                messages.warning(request, "We're sorry, ticket sales have closed")
                return redirect('index')

        form = TicketForm()
        self_form = TicketForSelfForm()
        others_formset = TicketForOthersFormSet()
        company_details_form = CompanyDetailsForm()

    context = {
        'form': form,
        'self_form': self_form,
        'others_formset': others_formset,
        'company_details_form': company_details_form,
        'user_can_buy_for_self': request.user.is_authenticated and not request.user.get_ticket(),
        'rates_table_data': _rates_table_data(),
        'rates_data': _rates_data(),
        'js_paths': ['tickets/order_form.js'],
    }

    return render(request, 'tickets/new_order.html', context)


@login_required
def order_confirm(request):

    details = request.session['ticket_details']

    if request.method == 'POST':

        print(details)

        invoice = actions.create_invoice_with_tickets(
            request.user,
            details['rate'],
            details['days_for_self'],
            details['email_addrs_and_days_for_others'],
            details['company_details'],
        )

        return redirect(invoice)

    else:

        RATES = {
            'INDI': 'Individual',
            'CORP': 'Corporate',
            'EDUC': 'Education',
        }

        order_total = Decimal()

        number_of_tickets = 0
        if details['email_addrs_and_days_for_others']:
            number_of_tickets += len(details['email_addrs_and_days_for_others'])
        if details['days_for_self']:
            number_of_tickets += 1

        rate = RATES[details['rate']]

        details_for_self = {}

        if details['days_for_self']:
            details_for_self['days'] = [DAYS[day] for day in details['days_for_self']]
            details_for_self['amount'] = cost_incl_vat(details['rate'], len(details['days_for_self']))
            order_total += details_for_self['amount']

        details_for_others = []
        if details['email_addrs_and_days_for_others']:
            for email, days in details['email_addrs_and_days_for_others']:
                details_for_others.append((
                    email,
                    [DAYS[day] for day in days],
                    cost_incl_vat(details['rate'], len(days))
                ))
                order_total += cost_incl_vat(details['rate'], len(days))

        context = {
            'rate': rate,
            'number_of_tickets': number_of_tickets,
            'details_for_self': details_for_self,
            'details_for_others': details_for_others,
            'order_total': order_total,
            'company_details': details['company_details'],
        }

        return render(request, 'tickets/order_confirm.html', context)


@login_required
def order_edit(request):

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
                request.session['ticket_details'] = {
                    'rate': rate,
                    'days_for_self': days_for_self,
                    'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
                    'company_details': company_details,
                    'form': form.data,
                    'self_form': self_form.data,
                    'others_formset': others_formset.data,
                    'company_details_form': company_details_form.data,
                }

                return redirect('tickets:order_confirm')

    else:
        form = TicketForm(request.session['ticket_details']['form'])
        self_form = TicketForSelfForm(request.session['ticket_details']['self_form'])
        others_formset = TicketForOthersFormSet(request.session['ticket_details']['others_formset'])
        company_details_form = CompanyDetailsForm(request.session['ticket_details']['company_details_form'])

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
def ticket(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)

    if request.user != ticket.owner:
        messages.warning(request, 'Only the owner of a ticket can view the ticket')
        return redirect('index')

    if ticket.is_free_ticket() and ticket.is_incomplete():
        return redirect('tickets:ticket_edit', ticket.ticket_id)

    if not request.user.profile_complete():
        messages.warning(request, mark_safe('Your profile is incomplete. <a href="{}">Update your profile</a>'.format(reverse('accounts:profile'))))

    context = {
        'ticket': ticket,
    }
    return render(request, 'tickets/ticket.html', context)


@login_required
def ticket_edit(request, ticket_id):
    ticket = Ticket.objects.get_by_ticket_id_or_404(ticket_id)

    if request.user != ticket.owner:
        messages.warning(request, 'Only the owner of a ticket can edit the ticket')
        return redirect('index')

    if not ticket.is_free_ticket():
        messages.warning(request, 'This ticket cannot be edited')
        return redirect(ticket)

    if request.method == 'POST':
        form = TicketForSelfForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            actions.update_free_ticket(ticket, days)
            return redirect(ticket)

    context = {
        'ticket': ticket,
        'form': TicketForSelfForm({'days': ticket.days_abbrev()}),
    }

    return render(request, 'tickets/ticket_edit.html', context)


def ticket_invitation(request, token):
    invitation = get_object_or_404(TicketInvitation, token=token)

    if not request.user.is_authenticated:
        messages.info(request, 'You need to create an account to claim your invitation')
        return redirect(reverse('register') + f'?next={invitation.get_absolute_url()}')

    if request.user.get_ticket() is not None:
        messages.error(request, 'You already have a ticket!  Please contact pyconuk-enquiries@python.org to arrange transfer of this invitaiton to somebody else.')
        return redirect('index')

    ticket = invitation.ticket

    if invitation.status == TicketInvitation.UNCLAIMED:
        assert ticket.owner is None
        actions.claim_ticket_invitation(request.user, invitation)
    elif invitation.status == TicketInvitation.CLAIMED:
        assert ticket.owner is not None
        messages.info(request, 'This invitation has already been claimed')
    else:
        assert False

    return redirect(ticket)


def _rates_data():
    return PRICES_INCL_VAT


def _rates_table_data():
    data = []
    data.append(['', 'Individual rate', 'Corporate rate', "Education rate"])
    for ix in range(5):
        num_days = ix + 1
        individual_rate = cost_incl_vat('INDI', num_days)
        corporate_rate = cost_incl_vat('CORP', num_days)
        education_rate = cost_incl_vat('EDUC', num_days)
        row = []
        if num_days == 1:
            row.append('1 day')
        else:
            row.append(f'{num_days} days')
        row.extend([f'£{individual_rate}', f'£{corporate_rate}', f'£{education_rate}'])
        data.append(row)

    return data
