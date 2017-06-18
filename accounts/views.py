import os

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import DemographicsProfileForm, RegisterForm, RequirementsProfileForm


with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'countries.txt')) as f:
    countries = [line.strip() for line in f]


@login_required
def profile(request):
    user = request.user

    context = {
        'name': user.name,
        'orders': user.orders.all(),
        'ticket': user.ticket(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = DemographicsProfileForm(request.POST, instance=user)
        if 'dont-ask-again' in request.POST:
            user.year_of_birth = None
            user.gender = None
            user.ethnicity = None
            user.nationality = None
            user.country_of_residence = None
            user.dont_ask_demographics = True
            user.save()
            return redirect('accounts:profile')

        if form.is_valid():
            user.dont_ask_demographics = False
            form.save()
            return redirect('accounts:profile')
    else:
        form = DemographicsProfileForm(instance=user)

    context = {
        'form': form,
        'js_paths': ['accounts/profile_form.js'],
        'countries': countries,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def edit_requirements_profile(request):
    user = request.user

    if request.method == 'POST':
        form = RequirementsProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = RequirementsProfileForm(instance=user)

    context = {
        'form': form,
        'js_paths': ['accounts/requirements_form.js'],
    }
    return render(request, 'accounts/edit_requirements_profile.html', context)


def register(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already signed in!')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                username=user.email_addr,
                password=form.cleaned_data['password1']
            )
            login(request, user)

            return redirect(request.POST.get('next', 'accounts:profile'))

    else:
        form = RegisterForm()

    context = {
        'form': form,
        'next': request.GET.get('next', 'accounts:profile'),
    }

    return render(request, 'registration/register.html', context)
