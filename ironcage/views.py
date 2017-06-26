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
        }
    else:
        context = {}

    return render(request, 'ironcage/index.html', context)
