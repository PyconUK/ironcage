from django.core.checks import Error
from django.test import override_settings, TestCase

from ..checks import env_vars_check


class EnvVarsCheckTest(TestCase):
    """Tests for env_vars_check."""
    def test_unset_in_prod(self):
        """When keys are unset, return an error for each."""
        errors = env_vars_check(None)
        expected = [
            Error('Env var "SECRET_KEY" must be set in production.'),
            Error('Env var "STRIPE_API_KEY_PUBLISHABLE" must be set in production.'),
            Error('Env var "STRIPE_API_KEY_SECRET" must be set in production.'),
        ]
        self.assertEqual(errors, expected)

    @override_settings(
        SECRET_KEY='changed',
        STRIPE_API_KEY_PUBLISHABLE='changed',
        STRIPE_API_KEY_SECRET='changed',
    )
    def test_set_in_prod(self):
        """If all's well in production, no need to return any errors."""
        errors = env_vars_check(None)
        self.assertEqual(errors, [])
