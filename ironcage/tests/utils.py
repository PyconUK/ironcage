from contextlib import contextmanager
import json
import os
from unittest.mock import patch

import stripe

from django.conf import settings


@contextmanager
def patched_charge_creation_success(amount_in_pence):
    path = os.path.join(settings.BASE_DIR, 'tickets', 'tests', 'data', 'stripe_charge_success.json')
    with open(path) as f:
        charge_data = json.load(f)
        if amount_in_pence:
            charge_data['amount'] = amount_in_pence
    charge = stripe.Charge.construct_from(charge_data, settings.STRIPE_API_KEY_PUBLISHABLE)
    with patch('stripe.Charge.create') as mock:
        mock.return_value = charge
        yield


@contextmanager
def patched_charge_creation_failure():
    card_error = stripe.error.CardError('Your card was declined.', None, 'card_declined')
    with patch('stripe.Charge.create') as mock:
        mock.side_effect = card_error
        yield


@contextmanager
def patched_refund_creation_expected():
    with patch('stripe.Refund.create') as mock:
        yield mock
    mock.assert_called()
