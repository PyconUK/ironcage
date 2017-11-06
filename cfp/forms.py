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
            'description_private',
            'aimed_at_new_programmers',
            'aimed_at_teachers',
            'aimed_at_data_scientists',
            'would_like_mentor',
            'would_like_longer_slot',
        ]

        labels = {
            'session_type': 'What are you proposing?',
            'copresenter_names': 'Are you presenting with anybody else?',
            'description': 'What is your session about?',
            'description_private': 'Is there anything else we should know about your proposal?',
            'aimed_at_new_programmers': 'new programmers?',
            'aimed_at_teachers': 'teachers?',
            'aimed_at_data_scientists': 'data scientists?',
            'would_like_mentor': 'like a mentor',
            'would_like_longer_slot': 'like to be considered for a longer talk slot',
        }

        help_texts = {
            'title': 'Limit: 60 characters.',
            'subtitle': 'Limit: 120 characters.  Optional.',
            'copresenter_names': 'If you are presenting with anybody else, please list their names here.',
            'description': 'If your session is selected, this is the basis of what will be published in the programme.  Limit: 300 words.',
            'description_private': 'Your answer here is for the benefit of the programme committee, and will not be published.  Limit: 300 words.',
        }

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': False}),
            'subtitle': forms.TextInput(attrs={'placeholder': False}),
            'copresenter_names': forms.Textarea(attrs={'cols': 40, 'rows': 3, 'placeholder': False}),
            'description': forms.Textarea(attrs={'placeholder': False}),
            'description_private': forms.Textarea(attrs={'placeholder': False}),
        }


class AcceptedForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'slide_url',
            'info_url',
            'video_url',
            'transcription',
        ]

        labels = {
            'copresenter_names': 'Are you presenting with anybody else?',
            'description': 'What is your session about?',
            'slide_url': 'At what URL can your slides be accessed?',
            'info_url': 'Do you have a URL for additional information?',
            'transcription': 'The transcription for your talk from the STTRs, if provided'
        }

        help_texts = {
            'slide_url': 'You do not need to fill this out until after your talk if you wish to.',
            'info_url': 'You do not need to fill this out until after your talk if you wish to.',
            'video_url': 'The conference team will update this field after the conference.',
            'transcription': 'The conference team will update this field after the conference, you may wish to edit the raw text to speech for accuracy and clarity.'
        }

        widgets = {
            'slide_url': forms.TextInput(attrs={'placeholder': False}),
            'info_url': forms.TextInput(attrs={'placeholder': False}),
            'video_url': forms.TextInput(attrs={'placeholder': False}),
            'transcription': forms.TextInput(attrs={'placeholder': False}),
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
