from django import forms

from ironcage.widgets import ButtonsRadio

from .models import Proposal


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'session_type',
            'title',
            'subtitle',
            'copresenter_names',
            'description',
            'outline',
            'description_private',
            'aimed_at_new_programmers',
            'aimed_at_teachers',
            'aimed_at_data_scientists',
            'would_like_mentor',
            'would_like_longer_slot',
            'coc_conformity',
        ]

        labels = {
            'session_type': 'What are you proposing?',
            'copresenter_names': 'Are you presenting with anybody else?',
            'description': 'What is your session about?',
            'outline': 'Can you give us an outline of your proposed session?',
            'description_private': 'Is there anything else we should know about your proposal?',
            'aimed_at_new_programmers': 'new programmers?',
            'aimed_at_teachers': 'teachers?',
            'aimed_at_data_scientists': 'data scientists?',
            'would_like_mentor': 'like a mentor',
            'would_like_longer_slot': 'like to be considered for a longer talk slot',
            'coc_conformity': 'Does your proposal conform to our Code of Conduct?',
        }

        help_texts = {
            'title': 'Limit: 60 characters.',
            'subtitle': 'Limit: 120 characters.  Optional.',
            'copresenter_names': 'If you are presenting with anybody else, please list their names here.',
            'description': 'If your session is selected, this is the basis of what will be published in the programme.  Limit: 300 words.',
            'outline': 'An outline of your session is optional, but helps the programme committee. A proposal with an outline is more likely to be selected than one without. More detail, including timings, is better. The outline will not be published.',
            'description_private': 'Your answer is for the benefit of the programme committee, and will not be published.  Limit: 300 words.',
            'coc_conformity': 'I confirm that my proposed session conforms to the requirements of the <a href="https://2018.pyconuk.org/code-conduct/" target="_blank">Code of Conduct</a>',
        }

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': False}),
            'subtitle': forms.TextInput(attrs={'placeholder': False}),
            'copresenter_names': forms.Textarea(attrs={'cols': 40, 'rows': 3, 'placeholder': False}),
            'description': forms.Textarea(attrs={'placeholder': False}),
            'outline': forms.Textarea(attrs={'placeholder': False}),
            'description_private': forms.Textarea(attrs={'placeholder': False}),
        }


IS_INTERESTED_CHOICES = [
    ('yes', 'Interested'),
    ('no', 'Not interested'),
    ('skip', 'Skip'),
]


class ProposalVotingForm(forms.Form):
    is_interested = forms.ChoiceField(
        choices=IS_INTERESTED_CHOICES,
        widget=ButtonsRadio
    )
