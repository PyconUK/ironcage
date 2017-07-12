from accounts.tests.factories import create_user

from ukpa.models import Nomination


def create_nomination(user=None):
    if user is None:
        user = create_user()

    return Nomination.objects.create(
        nominee=user,
        statement='Hello. I would like to be a UKPA Trustee.')
