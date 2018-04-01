from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse

from tickets.constants import DAYS

from ironcage.utils import Scrambler


class Application(models.Model):
    applicant = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='grant_application', on_delete=models.CASCADE)
    amount_requested = models.IntegerField()
    would_like_ticket_set_aside = models.BooleanField()
    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()
    tue = models.BooleanField()
    wed = models.BooleanField()
    about_you = models.TextField()
    amount_offered = models.IntegerField(default=0)
    requested_ticket_only = models.BooleanField(default=False)
    special_reply_required = models.BooleanField(default=False)

    id_scrambler = Scrambler(4000)

    class Manager(models.Manager):
        def get_by_application_id_or_404(self, application_id):
            id = self.model.id_scrambler.backward(application_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    @property
    def application_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('grants:application', args=[self.application_id])

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]
