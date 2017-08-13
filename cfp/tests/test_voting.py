from django.test import TestCase

from . import factories

from cfp.models import Proposal


class VotingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user('Alice')
        cls.bob = factories.create_user('Bob')
        cls.carol = factories.create_user('Carol')
        cls.proposals = [factories.create_proposal() for _ in range(4)]

        cls.proposals[0].vote(cls.alice, True)
        cls.proposals[1].vote(cls.alice, False)
        cls.proposals[0].vote(cls.bob, False)
        cls.proposals[2].vote(cls.bob, True)
        cls.proposals[0].vote(cls.carol, True)
        cls.proposals[3].vote(cls.carol, False)

    def test_vote(self):
        self.assertTrue(self.proposals[0].is_interested(self.alice))
        self.assertFalse(self.proposals[1].is_interested(self.alice))
        self.assertIsNone(self.proposals[2].is_interested(self.alice))

    def test_vote_again(self):
        self.proposals[0].vote(self.alice, False)

        self.assertFalse(self.proposals[0].is_interested(self.alice))

    def test_reviewed_by_user(self):
        self.assertSequenceEqual(
            Proposal.objects.reviewed_by_user(self.alice),
            [self.proposals[0], self.proposals[1]],
        )

    def test_unreviewed_by_user(self):
        self.assertSequenceEqual(
            Proposal.objects.unreviewed_by_user(self.alice),
            [self.proposals[2], self.proposals[3]],
        )

    def test_of_interest_to_user(self):
        self.assertSequenceEqual(
            Proposal.objects.of_interest_to_user(self.alice),
            [self.proposals[0]],
        )

    def test_not_of_interest_to_user(self):
        self.assertSequenceEqual(
            Proposal.objects.not_of_interest_to_user(self.alice),
            [self.proposals[1]],
        )

    def test_get_random_unreviewed_by_user(self):
        # There's a 1 in 2 ** 20 chance of this failing by accident...
        results = {Proposal.objects.get_random_unreviewed_by_user(self.alice) for _ in range(20)}
        self.assertSequenceEqual(
            results,
            {self.proposals[2], self.proposals[3]},
        )

    def test_get_random_unreviewed_by_user_when_all_proposals_reviewed(self):
        self.proposals[2].vote(self.alice, True)
        self.proposals[3].vote(self.alice, False)

        self.assertIsNone(Proposal.objects.get_random_unreviewed_by_user(self.alice))
