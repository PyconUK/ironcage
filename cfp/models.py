from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ironcage.utils import Scrambler
from ironcage.validators import validate_max_300_words


class Proposal(models.Model):
    SESSION_TYPE_CHOICES = (
        ('talk', 'A talk (25 minutes)'),
        ('workshop', 'A workshop (3 hours)'),
        ('poster', 'A poster'),
        ('other', 'Something else'),
    )

    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='proposals', on_delete=models.CASCADE)
    session_type = models.CharField(max_length=40, choices=SESSION_TYPE_CHOICES)
    title = models.CharField(max_length=60)
    subtitle = models.CharField(max_length=120, blank=True)
    copresenter_names = models.TextField(blank=True)
    description = models.TextField(validators=[validate_max_300_words])
    description_private = models.TextField(validators=[validate_max_300_words])
    aimed_at_new_programmers = models.BooleanField()
    aimed_at_teachers = models.BooleanField()
    aimed_at_data_scientists = models.BooleanField()
    would_like_mentor = models.BooleanField()
    would_like_longer_slot = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(3000)

    class Manager(models.Manager):
        def get_by_proposal_id_or_404(self, proposal_id):
            id = self.model.id_scrambler.backward(proposal_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    @property
    def proposal_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('cfp:proposal', args=[self.proposal_id])

    def full_title(self):
        if self.subtitle:
            return f'{self.title}: {self.subtitle}'
        else:
            return self.title
