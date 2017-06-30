from django.test import TestCase


class SettingsTests(TestCase):
    def test_prod_settings(self):
        import ironcage.settings.prod

    def test_staging_settings(self):
        import ironcage.settings.staging
