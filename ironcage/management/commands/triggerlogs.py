from django.core.management import BaseCommand

import structlog
logger = structlog.get_logger()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for level in ['critical', 'error', 'warning', 'info', 'debug']:
            fn = getattr(logger, level)
            fn(f'Logging at {level}')
