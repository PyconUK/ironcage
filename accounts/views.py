import os

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm


with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'countries.txt')) as f:
    countries = [line.strip() for line in f]


@login_required
def profile(request):
    user = request.user

    context = {
        'name': user.name,
        'orders': user.orders.all(),
        'ticket': user.get_ticket(),
        'show_sidebar': True,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'form': form,
        'js_paths': ['accounts/profile_form.js'],
        'countries': countries,
        'show_sidebar': True,
    }
    return render(request, 'accounts/edit_profile.html', context)


def register(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already signed in!')
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                username=user.email_addr,
                password=form.cleaned_data['password1']
            )
            login(request, user)

            return redirect(request.POST.get('next', 'index'))

    else:
        form = RegisterForm()

    context = {
        'form': form,
        'next': request.GET.get('next', 'index'),
    }

    return render(request, 'registration/register.html', context)
