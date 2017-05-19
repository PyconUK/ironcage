from django import forms
from django.forms import widgets


WHO_CHOICES = [
    ('self', 'Myself'),
    ('others', 'Other people'),
    ('self and others', 'Myself and other people'),
]


RATE_CHOICES = [
    ('individual', 'Individual'),
    ('corporate', 'Corporate'),
]


DAY_CHOICES = [
    ('thu', 'Thursday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
]


class ButtonsRadio(widgets.ChoiceWidget):
    template_name = 'tickets/widgets/buttons_radio.html'


class ButtonsCheckbox(widgets.ChoiceWidget):
    allow_multiple_selected = True
    template_name = 'tickets/widgets/buttons_checkbox.html'


class EmailInput(widgets.EmailInput):
    template_name = 'tickets/widgets/email_input.html'


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
        if any(self.errors):
            # No point cleaning if any forms have errors
            return

        self.email_addrs_and_days = []
        for form in self.forms:
            if not form.cleaned_data:
                # This was an empty form, so we ignore it
                continue

            email_addr = form.cleaned_data['email_addr']
            days = form.cleaned_data['days']
            self.email_addrs_and_days.append((email_addr, days))


TicketForOthersFormSet = forms.formset_factory(
    TicketForOtherForm,
    formset=BaseTicketForOthersFormset,
    min_num=1,
    extra=1,
    can_delete=True
)
