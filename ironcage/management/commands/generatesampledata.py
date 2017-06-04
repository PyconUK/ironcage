from django.core.management import BaseCommand, CommandError
from django.test import override_settings

from tickets.models import Order
from tickets.tests import factories


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if Order.objects.count() > 0:
            raise CommandError('The database is already populated')

        users = [factories.create_user(name) for name in ['Alice', 'Beatrice', 'Benedict']]

        with override_settings(EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend'):
            factories.create_ticket(users[0], num_days=5)
            factories.create_pending_order_for_others(users[0])
            factories.create_confirmed_order_for_self_and_others(users[1], rate='corporate')
            factories.create_confirmed_order_for_self(users[2], num_days=5)
