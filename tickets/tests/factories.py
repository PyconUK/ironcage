from accounts.models import User

from tickets import actions


def create_user(name='Alice'):
    email_addr = f'{name.lower()}@example.com'
    return User.objects.create_user(email_addr=email_addr, name=name)


def create_pending_order_for_self(user=None):
    user = user or create_user()
    return actions.create_pending_order(
        purchaser=user,
        rate='individual',
        days_for_self=['thu', 'fri', 'sat']
    )


def create_pending_order_for_others(user=None):
    user = user or create_user()
    return actions.create_pending_order(
        purchaser=user,
        rate='individual',
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['fri', 'sat']),
            ('carol@example.com', ['sat', 'sun']),
        ]
    )


def create_pending_order_for_self_and_others(user=None):
    user = user or create_user()
    return actions.create_pending_order(
        purchaser=user,
        rate='individual',
        days_for_self=['thu', 'fri', 'sat'],
        email_addrs_and_days_for_others=[
            ('bob@example.com', ['fri', 'sat']),
            ('carol@example.com', ['sat', 'sun']),
        ]
    )


def confirm_order(order):
    actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw')


def create_confirmed_order_for_self(user=None):
    order = create_pending_order_for_self(user)
    confirm_order(order)
    return order


def create_confirmed_order_for_others(user=None):
    order = create_pending_order_for_others(user)
    confirm_order(order)
    return order


def create_confirmed_order_for_self_and_others(user=None):
    order = create_pending_order_for_self_and_others(user)
    confirm_order(order)
    return order


def create_ticket(user=None):
    order = create_confirmed_order_for_self(user)
    return order.all_tickets()[0]
