from datetime import datetime, timezone

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProposalForm
from .models import Proposal


def new_proposal(request):
    if datetime.now(timezone.utc) > settings.CFP_CLOSE_AT:
        return _new_proposal_after_cfp_closes(request)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.proposer = request.user
            proposal.save()
            messages.success(request, 'Thank you for submitting your proposal')
            slack_message('cfp/proposal_created.slack', {'proposal': proposal})
            return redirect(proposal)
    else:
        form = ProposalForm()

    context = {
        'form': form,
        'js_paths': ['cfp/cfp_form.js'],
    }
    return render(request, 'cfp/new_proposal.html', context)


def _new_proposal_after_cfp_closes(request):
    if request.method == 'POST':
        messages.warning(request, "We're sorry, the Call For Participation has closed, and we were not able to process your submission")
    else:
        messages.warning(request, "We're sorry, the Call For Participation has closed")

    return redirect('index')


@login_required
def proposal_edit(request, proposal_id):
    if datetime.now(timezone.utc) > settings.CFP_CLOSE_AT:
        return _proposal_edit_after_cfp_closes(request, proposal_id)

    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can update the proposal')
        return redirect('index')

    if request.method == 'POST':
        form = ProposalForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save()
            proposal.save()
            messages.success(request, 'Thank you for updating your proposal')
            return redirect(proposal)
    else:
        form = ProposalForm(instance=proposal)

    context = {
        'form': form,
        'js_paths': ['cfp/cfp_form.js'],
    }
    return render(request, 'cfp/proposal_edit.html', context)


def _proposal_edit_after_cfp_closes(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.method == 'POST':
        messages.warning(request, "We're sorry, the Call For Participation has closed, and we were not able to process the change to your proposal")
    else:
        messages.warning(request, "We're sorry, the Call For Participation has closed, and we are not accepting any more changes to proposals")

    return redirect(proposal)


@login_required
def proposal(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can view the proposal')
        return redirect('index')

    context = {
        'proposal': proposal,
        'form': ProposalForm(),
        'cfp_open': datetime.now(timezone.utc) < settings.CFP_CLOSE_AT,
    }
    return render(request, 'cfp/proposal.html', context)


@login_required
@require_POST
def proposal_delete(request, proposal_id):

    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user == proposal.proposer:
        proposal.delete()
        messages.success(request, 'Your proposal has been withdrawn')
    else:
        messages.warning(request, 'Only the proposer of a proposal can withdraw the proposal')

    return redirect('index')
