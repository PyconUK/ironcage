from unittest import mock

from django.apps import apps
from django.test import TestCase

from ..apps import IroncageConfig
from ..checks import env_vars_check


class TestIroncageConfig(TestCase):
    def test_registered(self):
        """IroncageConfig is used as the config for the ironcage app."""
        self.assertIsInstance(apps.get_app_config('ironcage'), IroncageConfig)

    def test_checks_registered_on_ready(self):
        """The ready() method registers checks."""
        app_config = apps.get_app_config('ironcage')
        register_path = 'ironcage.apps.register'
        with mock.patch(register_path) as register:
            app_config.ready()

        register.assert_called_once_with(env_vars_check, deploy=True)
