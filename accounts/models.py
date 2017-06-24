from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from tickets.models import Ticket

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
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
    year_of_birth = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=100, null=True, blank=True)
    ethnicity = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    country_of_residence = models.CharField(max_length=100, null=True, blank=True)
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

    def ticket(self):
        try:
            return self.tickets.get()
        except Ticket.DoesNotExist:
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
