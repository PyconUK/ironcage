from django import forms
from django.core.exceptions import ValidationError

from ironcage.widgets import ButtonsCheckbox, ButtonsRadio, EmailInput

from tickets.models import Ticket


WHO_CHOICES = [
    ('self', 'Myself'),
    ('others', 'Other people'),
    ('self and others', 'Myself and other people'),
]


DAY_CHOICES = [
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
]

RATE_CHOICES = [
    (Ticket.INDIVIDUAL, 'Individual'),
    (Ticket.CORPORATE, 'Corporate'),
    (Ticket.EDUCATION, 'Education'),
]


class TicketForm(forms.Form):
    who = forms.ChoiceField(
        choices=WHO_CHOICES,
        widget=ButtonsRadio
    )
    rate = forms.ChoiceField(
        choices=RATE_CHOICES,
        widget=ButtonsRadio
    )


class TicketForSelfForm(forms.Form):
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )


class TicketForOtherForm(forms.Form):
    email_addr = forms.EmailField(
        widget=EmailInput(attrs={'class': 'form-control'}),
    )
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )


class BaseTicketForOthersFormset(forms.BaseFormSet):
    def clean(self):
        self.email_addrs_and_days = []
        for form in self.forms:
            if form.errors:
                continue

            if not form.cleaned_data:
                # This was an empty form, so we ignore it
                continue

            email_addr = form.cleaned_data['email_addr']
            days = form.cleaned_data['days']
            self.email_addrs_and_days.append((email_addr, days))

        if not self.email_addrs_and_days:
            raise ValidationError('No valid forms')


TicketForOthersFormSet = forms.formset_factory(
    TicketForOtherForm,
    formset=BaseTicketForOthersFormset,
    min_num=1,
    extra=1,
    can_delete=True
)


class CompanyDetailsForm(forms.Form):
    company_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    company_addr = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
