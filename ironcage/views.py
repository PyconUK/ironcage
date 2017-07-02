from django.contrib import messages
from django.shortcuts import render


def index(request):
    user = request.user

    if user.is_authenticated() and not user.profile_complete():
        if user.get_ticket() is not None:
            messages.warning(request, 'Your profile is incomplete')
        context = {
            'ticket': user.get_ticket(),
            'orders': user.orders.all(),
            'grant_application': user.get_grant_application(),
            'proposals': user.proposals.all(),
        }
    else:
        context = {}

    return render(request, 'ironcage/index.html', context)


def error(request):
    1 / 0
