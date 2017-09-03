from accounts.tests.factories import create_user

from tickets import actions


def create_pending_order_for_self(user=None, rate=None, num_days=None):
    user = user or create_user()
    rate = rate or 'individual'
    num_days = num_days or 3

    if rate == 'corporate':
        company_details = {
            'name': 'Sirius Cybernetics Corp.',
            'addr': 'Eadrax, Sirius Tau',
        }
    else:
        company_details = None

    return actions.create_pending_order(
        purchaser=user,
        rate=rate,
        days_for_self=['thu', 'fri', 'sat', 'sun', 'mon'][:num_days],
        company_details=company_details,
    )


def create_pending_order_for_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'individual'
    return actions.create_pending_order(
        purchaser=user,
        rate=rate,
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['fri', 'sat']),
            ('carol@example.com', ['sat', 'sun']),
        ]
    )


def create_pending_order_for_self_and_others(user=None, rate=None):
    user = user or create_user()
    rate = rate or 'individual'
    return actions.create_pending_order(
        purchaser=user,
        rate=rate,
        days_for_self=['thu', 'fri', 'sat'],
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['fri', 'sat']),
            ('carol@example.com', ['sat', 'sun']),
        ]
    )


def confirm_order(order):
    actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)


def mark_order_as_failed(order):
    actions.mark_order_as_failed(order, 'Your card was declined.')


def mark_order_as_errored_after_charge(order):
    actions.mark_order_as_errored_after_charge(order, 'ch_abcdefghijklmnopqurstuvw')


def create_confirmed_order_for_self(user=None, rate=None, num_days=None):
    order = create_pending_order_for_self(user, rate, num_days)
    confirm_order(order)
    return order


def create_confirmed_order_for_others(user=None, rate=None):
    order = create_pending_order_for_others(user, rate)
    confirm_order(order)
    return order


def create_confirmed_order_for_self_and_others(user=None, rate=None):
    order = create_pending_order_for_self_and_others(user, rate)
    confirm_order(order)
    return order


def create_failed_order(user=None, rate=None):
    order = create_pending_order_for_self(user, rate)
    mark_order_as_failed(order)
    return order


def create_errored_order(user=None, rate=None):
    order = create_pending_order_for_self(user, rate)
    mark_order_as_errored_after_charge(order)
    return order


def create_ticket(user=None, rate=None, num_days=None):
    order = create_confirmed_order_for_self(user, rate, num_days)
    return order.all_tickets()[0]


def create_free_ticket(email_addr=None, pot='Financial assistance'):
    if email_addr is None:
        email_addr = create_user().email_addr
    return actions.create_free_ticket(email_addr, pot)
