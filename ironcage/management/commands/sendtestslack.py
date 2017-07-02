from django_slack import slack_message

from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        slack_message('ironcage/test.slack')
