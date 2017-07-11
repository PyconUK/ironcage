from django import forms

from .models import Nomination


class NominationForm(forms.ModelForm):
    class Meta:
        model = Nomination
        fields = [
            'statement'
        ]

        labels = {
            'statement': 'Please make a statment in support of your nomination',
        }

        help_texts = {
            'statment': 'Limit: 300 words.',
        }

        widgets = {
            'statement': forms.Textarea(attrs={'placeholder': False}),
        }
