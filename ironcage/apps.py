from django.apps import AppConfig
from django.core.checks import register

from .checks import env_vars_check


class IroncageConfig(AppConfig):
    name = 'ironcage'

    def ready(self):
        register(env_vars_check, deploy=True)
