from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ironcage.utils import Scrambler
from ironcage.validators import validate_max_300_words


class Nomination(models.Model):

    nominee = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='nomination', on_delete=models.CASCADE)
    statement = models.TextField(validators=[validate_max_300_words])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(3000)

    class Manager(models.Manager):
        def get_by_nomination_id_or_404(self, proposal_id):
            id = self.model.id_scrambler.backward(proposal_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    @property
    def nomination_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('cfp:proposal', args=[self.proposal_id])
