from datetime import datetime, timedelta, timezone

from django.test import TestCase, override_settings

from accounts.tests import factories as account_factories
from cfp.tests import factories as cfp_factories
from dinners.tests import factories as dinners_factories
from grants.tests import factories as grants_factories
from tickets.tests import factories as ticket_factories


class IndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = account_factories.create_user()

    def setUp(self):
        self.client.force_login(self.alice)

    def test_when_not_signed_in(self):
        self.client.logout()

        rsp = self.client.get('/')
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order conference tickets</a>', html=True)
        self.assertNotContains(rsp, '<a href="/profile/">Update your profile</a>', html=True)

    def test_when_has_ticket(self):
        ticket = ticket_factories.create_ticket(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, 'You have a ticket for Saturday, Sunday, Monday')
        self.assertContains(rsp, f'<a href="/tickets/tickets/{ticket.ticket_id}/">View your conference ticket</a>', html=True)
        self.assertContains(rsp, '<a href="/profile/">Update your profile</a>', html=True)
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'We look forward to seeing you in Cardiff')

    def test_when_has_ticket_and_full_profile(self):
        user = account_factories.create_user_with_full_profile()
        ticket = ticket_factories.create_ticket(user)
        self.client.force_login(user)

        rsp = self.client.get('/')
        self.assertContains(rsp, f'<a href="/tickets/tickets/{ticket.ticket_id}/">View your conference ticket</a>', html=True)
        self.assertContains(rsp, '<a href="/profile/">Update your profile</a>', html=True)
        self.assertNotContains(rsp, 'Your profile is incomplete')

    def test_when_has_no_ticket(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'You have a ticket')
        self.assertNotContains(rsp, 'View your conference ticket')
        self.assertNotContains(rsp, 'Update your profile')
        self.assertContains(rsp, 'We hope to see you in Cardiff')

    def test_when_has_order(self):
        order = ticket_factories.create_paid_order_for_others(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, f'<a href="/tickets/orders/{order.order_id}/">View your order</a>', html=True)
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order more conference tickets</a>', html=True)

    def test_when_has_no_order(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'View your order')
        self.assertNotContains(rsp, 'Order more conference tickets')

    def test_when_has_multiple_orders(self):
        order1 = ticket_factories.create_paid_order_for_self(self.alice)
        order2 = ticket_factories.create_paid_order_for_others(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, f'<a href="/tickets/orders/{order1.order_id}/">Order {order1.order_id}</a> (1 individual-rate ticket)', html=True)
        self.assertContains(rsp, f'<a href="/tickets/orders/{order2.order_id}/">Order {order2.order_id}</a> (2 individual-rate tickets)', html=True)
        self.assertContains(rsp, '<a href="/tickets/orders/new/">Order more conference tickets</a>', html=True)

    def test_when_has_proposal(self):
        proposal = cfp_factories.create_proposal(self.alice)

        rsp = self.client.get('/')
        self.assertContains(rsp, '<a href="/cfp/proposals/new/">Make another proposal to our Call for Participation</a>', html=True)
        self.assertContains(rsp, f'<a href="/cfp/proposals/{proposal.proposal_id}/">View your proposal to our Call for Participation</a> ({proposal.title})', html=True)

    @override_settings(CFP_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_when_has_proposal_and_cfp_closed(self):
        cfp_factories.create_proposal(self.alice)

        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'Make another proposal to our Call for Participation')

    def test_when_has_no_proposal(self):
        rsp = self.client.get('/')
        self.assertContains(rsp, '<a href="/cfp/proposals/new/">Make a proposal to our Call for Participation</a>', html=True)

    @override_settings(CFP_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_when_has_no_proposal_and_cfp_closed(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'Make a proposal to our Call for Participation')

    def test_when_has_grant_application(self):
        application = grants_factories.create_application(self.alice)

        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'Apply for financial assistance')
        self.assertContains(rsp, f'<a href="/grants/applications/{application.application_id}/">View your application for financial assistance</a>', html=True)

    def test_when_has_no_grant_application(self):
        rsp = self.client.get('/')
        self.assertContains(rsp, '<a href="/grants/applications/new/">Apply for financial assistance</a>', html=True)
        self.assertNotContains(rsp, 'View your application for financial assistance')

    @override_settings(GRANT_APPLICATIONS_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_when_has_no_grant_application_and_applications_closed(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, 'Apply for financial assistance')

    def test_when_is_contributor_and_has_no_dinner_bookings(self):
        self.alice.is_contributor = True
        self.alice.save()

        rsp = self.client.get('/')
        self.assertContains(rsp, "Make a booking for the contributors' dinner")
        self.assertNotContains(rsp, 'Make a booking for the conference dinner')
        self.assertNotContains(rsp, "View your contributors' dinner booking")
        self.assertNotContains(rsp, 'View your conference dinner booking')

    def test_when_is_contributor_and_is_booked_for_contributors_dinner(self):
        self.alice.is_contributor = True
        self.alice.save()
        dinners_factories.create_contributors_booking(self.alice)

        rsp = self.client.get('/')
        self.assertNotContains(rsp, "Make a booking for the contributors' dinner")
        self.assertContains(rsp, 'Make a booking for the conference dinner')
        self.assertContains(rsp, "View your contributors' dinner booking")
        self.assertNotContains(rsp, 'View your conference dinner booking')

    def test_when_is_contributor_and_is_booked_for_conference_dinner(self):
        self.alice.is_contributor = True
        self.alice.save()
        dinners_factories.create_contributors_booking(self.alice, 'conference')

        rsp = self.client.get('/')
        self.assertNotContains(rsp, "Make a booking for the contributors' dinner")
        self.assertNotContains(rsp, 'Make a booking for the conference dinner')
        self.assertNotContains(rsp, "View your contributors' dinner booking")
        self.assertContains(rsp, 'View your conference dinner booking')

    def test_when_is_contributor_and_is_booked_for_both_dinners(self):
        self.alice.is_contributor = True
        self.alice.save()
        dinners_factories.create_contributors_booking(self.alice)
        dinners_factories.create_paid_booking(self.alice)

        rsp = self.client.get('/')
        self.assertNotContains(rsp, "Make a booking for the contributors' dinner")
        self.assertNotContains(rsp, 'Make a booking for the conference dinner')
        self.assertContains(rsp, "View your contributors' dinner booking")
        self.assertContains(rsp, 'View your conference dinner booking')

    def test_when_is_not_contributor_and_has_no_dinner_bookings(self):
        rsp = self.client.get('/')
        self.assertNotContains(rsp, "Make a booking for the contributors' dinner")
        self.assertContains(rsp, 'Make a booking for the conference dinner')
        self.assertNotContains(rsp, "View your contributors' dinner booking")
        self.assertNotContains(rsp, 'View your conference dinner booking')

    def test_when_is_not_contributor_and_is_booked_for_conference_dinner(self):
        dinners_factories.create_paid_booking(self.alice)
        rsp = self.client.get('/')
        self.assertNotContains(rsp, "Make a booking for the contributors' dinner")
        self.assertNotContains(rsp, 'Make a booking for the conference dinner')
        self.assertNotContains(rsp, "View your contributors' dinner booking")
        self.assertContains(rsp, 'View your conference dinner booking')
