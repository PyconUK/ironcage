from django.test import TestCase


class SettingsTests(TestCase):
    def test_prod_settings(self):
        import ironcage.settings.prod  # noqa

    def test_staging_settings(self):
        import ironcage.settings.staging  # noqa
