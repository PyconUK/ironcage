from django import forms
from django.contrib.auth import password_validation

from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput,
        strip=False,
        help_text='Enter the same password as before, for verification.',
    )

    error_messages = {
        'password_mismatch': "The two password fields didn't match.",
    }

    class Meta:
        model = User
        fields = [
            'email_addr',
            'name',
            'password1',
            'password2'
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        self.instance.username = self.cleaned_data.get('username')
        password_validation.validate_password(self.cleaned_data.get('password2'), self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'name',
            'email_addr',
            'accessibility_reqs_yn',
            'accessibility_reqs',
            'childcare_reqs_yn',
            'childcare_reqs',
            'dietary_reqs_yn',
            'dietary_reqs',
            'dont_ask_demographics',
            'year_of_birth',
            'gender',
            'ethnicity',
            'nationality',
            'country_of_residence',
        ]

    def clean(self):
        super().clean()
        if self.cleaned_data.get('dont_ask_demographics'):
            for key in [
                'year_of_birth',
                'gender',
                'ethnicity',
                'nationality',
                'country_of_residence',
            ]:
                self.cleaned_data[key] = None
