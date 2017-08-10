import io

from django_slack import slack_message
import pandas as pd

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProposalForm
from .models import Proposal


def new_proposal(request):
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


@login_required
def proposal_edit(request, proposal_id):
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


@login_required
def proposal(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)

    if request.user != proposal.proposer:
        messages.warning(request, 'Only the proposer of a proposal can view the proposal')
        return redirect('index')

    context = {
        'proposal': proposal,
        'form': ProposalForm(),
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


@login_required
def histogram(request):
    records = [[proposal.created_at.date()] for proposal in Proposal.objects.all()]
    df = pd.DataFrame.from_records(records, columns=['date'])
    df['date'] = df['date'].astype('datetime64[ns]')
    plot = df.groupby(df['date'].dt.date).count().plot(kind='bar')
    fig = plot.get_figure()
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    response = HttpResponse(svg, content_type='image/svg+xml')
    return response
