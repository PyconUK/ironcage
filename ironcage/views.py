from django.contrib import messages
from django.shortcuts import render


def index(request):
    user = request.user

    if user.is_authenticated():
        context = {
            'orders': user.orders.all(),
            'ticket': user.ticket(),
        }

        if not user.profile_complete():
            messages.warning(request, 'Your profile is incomplete')
    else:
        context = {}

    return render(request, 'ironcage/index.html', context)
