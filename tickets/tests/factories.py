from accounts.models import User

from tickets import actions


def create_user(name='Alice'):
    email_addr = f'{name.lower()}@example.com'
    return User.objects.create_user(email_addr=email_addr, name=name)


def create_pending_order_for_self(user=None, rate=None, num_days=None):
    user = user or create_user()
    rate = rate or 'individual'
    num_days = num_days or 3
    return actions.create_pending_order(
        purchaser=user,
        rate=rate,
        days_for_self=['thu', 'fri', 'sat', 'sun', 'mon'][:num_days]
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


def create_ticket(user=None, rate=None, num_days=None):
    order = create_confirmed_order_for_self(user, rate, num_days)
    return order.all_tickets()[0]
