from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegisterForm


@login_required
def profile(request):
    user = request.user

    context = {
        'name': user.name,
        'ticket': user.ticket(),
    }
    return render(request, 'accounts/profile.html', context)


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

            return redirect(request.GET.get('next', 'accounts:profile'))

    else:
        form = RegisterForm()

    context = {
        'form': form,
    }

    return render(request, 'registration/register.html', context)
