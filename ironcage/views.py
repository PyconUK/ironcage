from django.shortcuts import render


def index(request):
    if request.user.is_authenticated():
        pass
    else:
        pass
    return render(request, 'ironcage/index.html')
