from django import forms

from ironcage.widgets import ButtonsRadio

from .menus import MENUS


WHICH_DINNER_CHOICES = [
    ('contributors', "Contributors' Dinner"),
    ('conference', 'Conference Dinner'),
]


class WhichDinnerForm(forms.Form):
    which_dinner = forms.ChoiceField(
        choices=WHICH_DINNER_CHOICES,
        widget=ButtonsRadio
    )


class ContributorsDinnerForm(forms.Form):
    starter = forms.ChoiceField(
        choices=MENUS['contributors']['starter'],
    )
    main = forms.ChoiceField(
        choices=MENUS['contributors']['main'],
    )
    pudding = forms.ChoiceField(
        choices=MENUS['contributors']['pudding'],
    )


class ConferenceDinnerForm(forms.Form):
    starter = forms.ChoiceField(
        choices=MENUS['conference']['starter'],
    )
    main = forms.ChoiceField(
        choices=MENUS['conference']['main'],
    )
    pudding = forms.ChoiceField(
        choices=MENUS['conference']['pudding'],
    )
