from django.contrib import messages
from django.shortcuts import render


def index(request):
    user = request.user

    if user.is_authenticated() and not user.profile_complete():
        messages.warning(request, 'Your profile is incomplete')

    return render(request, 'ironcage/index.html')
