from datetime import datetime

from django.core.management import BaseCommand

from ...emails import send_mail


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('to_addr')

    def handle(self, *args, to_addr, **kwargs):
        send_mail(
            'PyCon UK 2018 test email',
            f'This is a test, generated at {datetime.now()}',
            to_addr,
        )
