import json
import os

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from grants.models import Application
from tickets.models import Ticket

from .managers import UserManager


# https://en.wikipedia.org/wiki/Member_states_of_the_United_Nations
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'countries.txt')) as f:
    COUNTRIES = [line.strip() for line in f]

# https://en.wikipedia.org/wiki/List_of_adjectival_and_demonymic_forms_for_countries_and_nations
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'nationalities.txt')) as f:
    NATIONALITIES = [line.strip() for line in f]

# https://www.ons.gov.uk/ons/guide-method/harmonisation/primary-set-of-harmonised-concepts-and-questions/ethnic-group.pdf
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'ethnicities.json')) as f:
    ETHNICITIES = json.load(f)


class User(AbstractBaseUser, PermissionsMixin):
    YEAR_OF_BIRTH_CHOICES = [['not shared', 'prefer not to say']] + [[str(year), str(year)] for year in range(1917, 2017)]

    GENDER_CHOICES = [
        ['not shared', 'prefer not to say'],
        ['female', 'female'],
        ['male', 'male'],
        ['other', 'please specify'],
    ]

    COUNTRY_CHOICES = [['not shared', 'prefer not to say']] + [[country, country] for country in COUNTRIES] + [['other', 'not listed here (please specify)']]

    NATIONALITY_CHOICES = [['not shared', 'prefer not to say']] + [[nationality, nationality] for nationality in NATIONALITIES] + [['other', 'not listed here (please specify)']]

    # Sorry
    ETHNICITY_CHOICES = [['not shared', 'prefer not to say']] + [[ethnicity_category, [[ethnicity, ethnicity] for ethnicity in ethnicities]] for ethnicity_category, ethnicities in ETHNICITIES]

    email_addr = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'That email address has already been registered',
        },
    )
    name = models.CharField(max_length=200)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    year_of_birth = models.CharField(max_length=10, null=True, blank=True, choices=YEAR_OF_BIRTH_CHOICES)
    gender = models.CharField(max_length=100, null=True, blank=True, choices=GENDER_CHOICES)
    ethnicity = models.CharField(max_length=100, null=True, blank=True, choices=ETHNICITY_CHOICES)
    ethnicity_free_text = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True, choices=NATIONALITY_CHOICES)
    country_of_residence = models.CharField(max_length=100, null=True, blank=True, choices=COUNTRY_CHOICES)
    dont_ask_demographics = models.BooleanField(default=False)
    accessibility_reqs_yn = models.NullBooleanField()
    accessibility_reqs = models.TextField(null=True, blank=True)
    childcare_reqs_yn = models.NullBooleanField()
    childcare_reqs = models.TextField(null=True, blank=True)
    dietary_reqs_yn = models.NullBooleanField()
    dietary_reqs = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email_addr'
    EMAIL_FIELD = 'email_addr'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def get_full_name(self):
        '''This is used by the admin.'''
        return self.name

    def get_short_name(self):
        '''This is used by the admin.'''
        return self.name

    def get_ticket(self):
        try:
            return self.ticket
        except Ticket.DoesNotExist:
            return None

    def get_grant_application(self):
        try:
            return self.grant_application
        except Application.DoesNotExist:
            return None

    def profile_complete(self):
        if any(v is None for v in [
            self.accessibility_reqs_yn,
            self.childcare_reqs_yn,
            self.dietary_reqs_yn,
        ]):
            return False

        if self.dont_ask_demographics:
            return True

        return all(v for v in [
            self.year_of_birth,
            self.gender,
            self.ethnicity,
            self.nationality,
            self.country_of_residence
        ])
