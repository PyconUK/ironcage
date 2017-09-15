from accounts.tests.factories import create_user

from cfp.models import Proposal


def create_proposal(user=None, session_type='talk', state='accepted'):
    if user is None:
        user = create_user()

    return Proposal.objects.create(
        proposer=user,
        session_type=session_type,
        state=state,
        title='Python is brilliant',
        subtitle='From abs to ZeroDivisionError',
        copresenter_names='',
        description='Let me tell you why Python is brilliant',
        description_private='I am well placed to tell you why Python is brilliant',
        aimed_at_new_programmers=True,
        aimed_at_teachers=False,
        aimed_at_data_scientists=False,
        would_like_mentor=True,
        would_like_longer_slot=False,
    )
