from django.test import TestCase


class SettingsTests(TestCase):
    def test_prod_settings(self):
        # Test that prod settings can be imported
        import ironcage.settings.prod  # noqa

    def test_staging_settings(self):
        # Test that staging settings can be imported
        import ironcage.settings.staging  # noqa
