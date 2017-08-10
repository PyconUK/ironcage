from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'adult_name',
            'adult_email_addr',
            'adult_phone_number',
            'accessibility_reqs',
            'dietary_reqs',
        ]


class TicketForm(forms.Form):
    name = forms.CharField()
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


TicketFormSet = forms.formset_factory(
    TicketForm,
    min_num=1,
    extra=0,
    can_delete=True
)
