from datetime import datetime, timezone

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProposalForm, ProposalVotingForm
from .models import Proposal


def _can_submit(request):
    if datetime.now(timezone.utc) <= settings.CFP_CLOSE_AT:
        return True

    if request.GET.get('deadline-bypass-token', '') == settings.CFP_DEADLINE_BYPASS_TOKEN:
        return True

    return False


def new_proposal(request):
    if not _can_submit(request):
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
    if not _can_submit(request):
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
        'cfp_open': _can_submit(request),
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


def user_has_ticket(user):
    return user.is_authenticated and user.get_ticket()


@user_passes_test(user_has_ticket)
def voting_index(request):
    proposal = Proposal.objects.get_random_unreviewed_by_user(request.user)
    if proposal is None:
        messages.success(request, "You've reviewed all the talks, thank you!")
        return redirect('cfp:voting_reviewed_proposals')
    else:
        return redirect('cfp:voting_proposal', proposal_id=proposal.proposal_id)


@user_passes_test(user_has_ticket)
def voting_reviewed_proposals(request):
    context = {
        'proposals': Proposal.objects.reviewed_by_user(request.user),
        'title': "Talks you've reviewed",
        'empty_message': "You haven't reviewed any talks yet.",
    }

    context.update(_voting_stats(request.user))

    return render(request, 'cfp/voting/proposals.html', context)


@user_passes_test(user_has_ticket)
def voting_unreviewed_proposals(request):
    context = {
        'proposals': Proposal.objects.unreviewed_by_user(request.user),
        'title': "Talks you've not reviewed",
        'empty_message': "You've reviewed all the talks!",
    }

    context.update(_voting_stats(request.user))

    return render(request, 'cfp/voting/proposals.html', context)


@user_passes_test(user_has_ticket)
def voting_proposals_of_interest(request):
    context = {
        'proposals': Proposal.objects.of_interest_to_user(request.user),
        'title': "Talks you're interested in attending",
        'empty_message': "You've not indicated that you're interested in any talks.",
    }

    context.update(_voting_stats(request.user))

    return render(request, 'cfp/voting/proposals.html', context)


@user_passes_test(user_has_ticket)
def voting_proposals_not_of_interest(request):
    context = {
        'proposals': Proposal.objects.not_of_interest_to_user(request.user),
        'title': "Talks you're not interested in attending",
        'empty_message': "You've not indicated that you're not interested in any talks.",
    }

    context.update(_voting_stats(request.user))

    return render(request, 'cfp/voting/proposals.html', context)


@user_passes_test(user_has_ticket)
def voting_proposal(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.method == 'POST':
        is_interested = request.POST['is_interested']

        if is_interested == 'yes':
            proposal.vote(request.user, True)
        elif is_interested == 'no':
            proposal.vote(request.user, False)
        elif is_interested == 'skip':
            pass

        return redirect('cfp:voting_index')

    form = ProposalVotingForm({
        'is_interested': proposal.is_interested_for_form(request.user),
    })

    context = {
        'proposal': proposal,
        'form': form,
        'js_paths': ['cfp/voting_form.js'],
    }

    context.update(_voting_stats(request.user))

    return render(request, 'cfp/voting/proposal.html', context)


def _voting_stats(user):
    return {
        'num_unreviewed': Proposal.objects.unreviewed_by_user(user).count(),
        'num_reviewed': Proposal.objects.reviewed_by_user(user).count(),
        'num_of_interest': Proposal.objects.of_interest_to_user(user).count(),
        'num_not_of_interest': Proposal.objects.not_of_interest_to_user(user).count(),
    }
