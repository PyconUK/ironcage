from datetime import datetime

from django.core.mail import send_mail
from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('to_addr')

    def handle(self, *args, **kwargs):
        send_mail(
            'PyCon UK 2017 test email',
            f'This is a test, generated at {datetime.now()}',
            'PyCon UK 2017 <noreply@pyconuk.org>',
            [kwargs['to_addr']],
            fail_silently=False,
        )
