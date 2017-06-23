from django.shortcuts import render


def index(request):
    user = request.user

    if user.is_authenticated():
        context = {
            'orders': user.orders.all(),
            'ticket': user.ticket(),
        }
    else:
        context = {}

    return render(request, 'ironcage/index.html', context)
