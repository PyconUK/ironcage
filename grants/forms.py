from django import forms

from ironcage.widgets import ButtonsCheckbox

from .models import Application


DAY_CHOICES = [
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
]


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'amount_requested',
            'would_like_ticket_set_aside',
            'about_you',
        ]

        labels = {
            'amount_requested': 'How much are you asking for?',
            'would_like_ticket_set_aside': 'Would you like a ticket set aside for you until your grant is allocated?',
            'about_you': 'Tell us a little bit about yourself!',
        }

        help_texts = {
            'amount_requested': 'Please give the amount of money (in GBP) you would require to attend the conference',
            'would_like_ticket_set_aside': 'If you cannot afford a ticket without assistance, we will reserve a ticket until your application is processed',
            'about_you': 'Let us know just a little bit about why attending PyCon UK would be important to you. Feel free to elaborate a little bit about who you are and what you do, as well.',
        }

        widgets = {
            'amount_requested': forms.NumberInput(attrs={'placeholder': False}),
            'about_you': forms.Textarea(attrs={'placeholder': False}),
        }

    days = forms.MultipleChoiceField(
        required=False,
        choices=DAY_CHOICES,
        widget=ButtonsCheckbox
    )
