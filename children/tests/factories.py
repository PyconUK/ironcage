from accounts.tests.factories import create_user

from children import actions


def create_pending_order(user=None):
    user = user or create_user()

    unconfirmed_details = [
        ['Percy Pea', '2012-01-01'],
    ]

    return actions.create_pending_order(
        purchaser=user,
        adult_name=user.name,
        adult_phone_number='07123 456789',
        adult_email_addr=user.email_addr,
        accessibility_reqs=None,
        dietary_reqs=None,
        unconfirmed_details=unconfirmed_details,
    )


def create_confirmed_order(user=None):
    order = create_pending_order(user)
    confirm_order(order)
    return order


def confirm_order(order):
    actions.confirm_order(order, 'ch_abcdefghijklmnopqurstuvw', 1495355163)
