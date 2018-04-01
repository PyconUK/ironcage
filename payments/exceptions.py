class InvoiceAlreadyPaidException(Exception):
    pass


class InvoiceHasPaymentsException(Exception):
    pass


class ItemNotOnInvoiceException(Exception):
    pass
