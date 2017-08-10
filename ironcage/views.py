from datetime import datetime, timezone

import structlog

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render


logger = structlog.get_logger()


def index(request):
    user = request.user

    if user.is_authenticated():
        if user.get_ticket() is not None and not user.profile_complete():
            messages.warning(request, 'Your profile is incomplete')
        context = {
            'ticket': user.get_ticket(),
            'orders': user.orders.all(),
            'grant_application': user.get_grant_application(),
            'proposals': user.proposals.all(),
            'nomination': user.get_nomination(),
            'cfp_open': datetime.now(timezone.utc) < settings.CFP_CLOSE_AT,
        }
    else:
        context = {}

    return render(request, 'ironcage/index.html', context)


def error(request):
    1 / 0


def log(request):
    logger.info('Test log')
    return redirect('index')
