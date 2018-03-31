from accounts.tests.factories import create_user

from grants.models import Application


def create_application(user=None):
    if user is None:
        user = create_user()

    return Application.objects.create(
        applicant=user,
        amount_requested=1000,
        would_like_ticket_set_aside=False,
        sat=True,
        sun=True,
        mon=True,
        tue=False,
        wed=False,
        about_you='I have two thumbs',
    )
