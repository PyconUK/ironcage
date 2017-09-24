from django.core.management import BaseCommand

from ...actions import refund_order
from ...models import Order


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('order_id')

    def handle(self, *args, order_id, **kwargs):
        order = Order.objects.get_by_order_id_or_404(order_id)
        refund_order(order)
