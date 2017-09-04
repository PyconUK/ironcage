PRICES_EXCL_VAT = {
    'free': {
        'ticket_price': 0,
        'day_price': 0,
    },
    'individual': {
        'ticket_price': 15,
        'day_price': 30,
    },
    'corporate': {
        'ticket_price': 30,
        'day_price': 60,
    },
    'education': {
        'ticket_price': 5,
        'day_price': 10,
    },
}

VAT_RATE = 0.2

PRICES_INCL_VAT = {}

for rate in PRICES_EXCL_VAT:
    PRICES_INCL_VAT[rate] = {}
    for price_type in ['ticket_price', 'day_price']:
        cost = PRICES_EXCL_VAT[rate][price_type] * (1 + VAT_RATE)
        assert cost == int(cost)
        PRICES_INCL_VAT[rate][price_type] = int(cost)


def cost_excl_vat(rate, num_days):
    prices = PRICES_EXCL_VAT[rate]
    return prices['ticket_price'] + prices['day_price'] * num_days


def cost_incl_vat(rate, num_days):
    prices = PRICES_INCL_VAT[rate]
    return prices['ticket_price'] + prices['day_price'] * num_days
