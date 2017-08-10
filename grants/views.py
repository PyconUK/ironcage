from datetime import datetime, timezone

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from tickets.constants import DAYS

from .forms import ApplicationForm
from .models import Application


def new_application(request):
    if datetime.now(timezone.utc) > settings.GRANT_APPLICATIONS_CLOSE_AT:
        return _new_application_after_cfp_closes(request)

    if request.user.is_authenticated and request.user.get_grant_application():
        messages.warning(request, 'You have already submitted an application')
        return redirect(request.user.get_grant_application())

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            for day in DAYS:
                if day in form.cleaned_data['days']:
                    setattr(application, day, True)
                else:
                    setattr(application, day, False)
            application.applicant = request.user
            application.save()
            messages.success(request, 'Thank you for submitting your application')
            slack_message('grants/application_created.slack', {'application': application})
            return redirect(application)
    else:
        form = ApplicationForm()

    context = {
        'form': form,
    }
    return render(request, 'grants/new_application.html', context)


def _new_application_after_cfp_closes(request):
    if request.method == 'POST':
        messages.warning(request, "We're sorry, financial assistance applications are closed, and we were not able to process your submission")
    else:
        messages.warning(request, "We're sorry, financial assistance applications are closed")

    return redirect('index')


@login_required
def application_edit(request, application_id):
    if datetime.now(timezone.utc) > settings.GRANT_APPLICATIONS_CLOSE_AT:
        return _application_edit_after_cfp_closes(request, application_id)

    application = Application.objects.get_by_application_id_or_404(application_id)

    if request.user != application.applicant:
        messages.warning(request, 'Only the owner of a application can update the application')
        return redirect('index')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            for day in DAYS:
                if day in form.cleaned_data['days']:
                    setattr(application, day, True)
                else:
                    setattr(application, day, False)
            application.save()
            messages.success(request, 'Thank you for updating your application')
            return redirect(application)
    else:
        data = model_to_dict(application)
        data['days'] = [day for day in DAYS if getattr(application, day)]
        form = ApplicationForm(data)

    context = {
        'form': form,
    }
    return render(request, 'grants/application_edit.html', context)


def _application_edit_after_cfp_closes(request, application_id):
    application = Application.objects.get_by_application_id_or_404(application_id)

    if request.method == 'POST':
        messages.warning(request, "We're sorry, financial assistance applications are closed, and we were not able to process the change to your application")
    else:
        messages.warning(request, "We're sorry, financial assistance applications are closed, and we are not accepting any more changes to applications")

    return redirect(application)


@login_required
def application(request, application_id):
    application = Application.objects.get_by_application_id_or_404(application_id)

    if request.user != application.applicant:
        messages.warning(request, 'Only the owner of a application can view the application')
        return redirect('index')

    context = {
        'application': application,
        'form': ApplicationForm(),
        'applications_open': datetime.now(timezone.utc) < settings.GRANT_APPLICATIONS_CLOSE_AT,
    }
    return render(request, 'grants/application.html', context)


@login_required
@require_POST
def application_delete(request, application_id):
    application = Application.objects.get_by_application_id_or_404(application_id)

    if request.user == application.applicant:
        application.delete()
        messages.success(request, 'Your application has been withdrawn')
    else:
        messages.warning(request, 'Only the owner of a application can delete the application')

    return redirect('index')
