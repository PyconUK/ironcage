from django.conf import settings
from django.core.checks import Error


def env_vars_check(app_configs, **kwargs):
    """Ensure critical env vars are set in production."""
    errors = []
    for watched in settings.ENVVAR_WATCHED:
        if getattr(settings, watched) == settings.ENVVAR_SENTINAL:
            msg = 'Env var "{}" must be set in production.'.format(watched)
            errors.append(Error(msg))
    return errors
