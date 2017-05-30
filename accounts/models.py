from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

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
