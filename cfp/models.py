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
    state = models.CharField(max_length=40, blank=True)
    track = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(3000)

    class Meta:
        permissions = [
            ('review_proposal', 'Can review proposals'),
        ]

    class Manager(models.Manager):
        def get_by_proposal_id_or_404(self, proposal_id):
            id = self.model.id_scrambler.backward(proposal_id)
            return get_object_or_404(self.model, pk=id)

        def reviewed_by_user(self, user):
            return self.filter(vote__user=user).order_by('id')

        def unreviewed_by_user(self, user):
            return self.exclude(vote__user=user).order_by('id')

        def of_interest_to_user(self, user):
            return self.filter(vote__user=user, vote__is_interested=True).order_by('id')

        def not_of_interest_to_user(self, user):
            return self.filter(vote__user=user, vote__is_interested=False).order_by('id')

        def get_random_unreviewed_by_user(self, user):
            return self.unreviewed_by_user(user).order_by('?').first()

    objects = Manager()

    def __str__(self):
        return self.proposal_id

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

    def is_accepted(self):
        return self.state == 'plan to accept'

    def is_rejected(self):
        return self.state == 'plan to reject'

    def session_type_for_display(self):
        if self.session_type == 'other':
            return 'a one-off session'
        else:
            return self.SESSION_TYPE_CHOICES[self.session_type].lower()

    def vote(self, user, is_interested):
        self.vote_set.update_or_create(
            user=user,
            defaults={
                'is_interested': is_interested,
            },
        )

    def is_interested(self, user):
        try:
            vote = self.vote_set.get(user=user)
        except Vote.DoesNotExist:
            return None

        return vote.is_interested

    def is_interested_for_form(self, user):
        is_interested = self.is_interested(user)

        if is_interested is True:
            return 'yes'
        elif is_interested is False:
            return 'no'


class Vote(models.Model):
    proposal = models.ForeignKey('Proposal')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    is_interested = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('proposal', 'user')

    def __str__(self):
        args = [
            self.user.email,
            'interested' if self.is_interested else 'not interested',
            self.proposal.title,
        ]
        return '{} was {} in {}'.format(*args)
