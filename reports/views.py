from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .reports import reports


@staff_member_required(login_url='login')
def index(request):
    return render(request, 'reports/index.html', {'reports': reports})
