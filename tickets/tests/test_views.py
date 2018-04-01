from datetime import (
    datetime,
    timedelta,
    timezone,
)
from unittest import skip

from django.test import (
    override_settings,
    TestCase,
)

from ironcage.tests import utils
from tickets import actions
from tickets.tests import factories
from tickets.models import TicketInvitation, Ticket


class NewOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def test_get(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/tickets/orders/new/')
        self.assertInHTML('<tr><td class="text-center">5 days</td><td class="text-center">£198</td><td class="text-center">£396</td><td class="text-center">£66</td></tr>', rsp.content.decode())
        self.assertContains(rsp, '<form method="post" id="order-form">')
        self.assertNotContains(rsp, 'to buy a ticket')

    @override_settings(TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1))
    def test_get_when_ticket_sales_have_closed(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/tickets/orders/new/', follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_but_correct_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/tickets/orders/new/?deadline-bypass-token=abc123', follow=True)
        self.assertNotContains(rsp, 'ticket sales have closed')
        self.assertContains(rsp, '<form method="post" id="order-form">')

    @override_settings(
        TICKET_SALES_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1),
        TICKET_DEADLINE_BYPASS_TOKEN='abc123',
    )
    def test_get_when_ticket_sales_have_closed_and_incorrect_token_is_provided(self):
        self.client.force_login(self.alice)
        rsp = self.client.get('/tickets/orders/new/?deadline-bypass-token=321cba', follow=True)
        self.assertContains(rsp, 'ticket sales have closed')
        self.assertRedirects(rsp, '/')

    def test_get_when_user_has_order_for_self(self):
        self.client.force_login(self.alice)
        factories.create_confirmed_order_for_self(self.alice)
        rsp = self.client.get('/tickets/orders/new/')
        self.assertNotContains(rsp, '<input type="radio" name="who" value="self">')
        self.assertContains(rsp, '<input type="hidden" name="who" value="others">')

    def test_get_when_user_has_order_but_not_for_self(self):
        self.client.force_login(self.alice)
        factories.create_confirmed_order_for_others(self.alice)
        rsp = self.client.get('/tickets/orders/new/')
        self.assertContains(rsp, '<input type="radio" name="who" value="self">')
        self.assertNotContains(rsp, '<input type="hidden" name="who" value="others">')

    def test_post_for_self_individual(self):
        self.client.force_login(self.alice)
        form_data = {
            'who': 'self',
            'rate': Ticket.INDIVIDUAL,
            'days': ['sat', 'sun', 'mon'],
            # The formset gets POSTed even when order is only for self
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': '',
            'form-1-email_addr': '',
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 1 ticket')

    def test_post_for_self_corporate(self):
        self.client.force_login(self.alice)
        form_data = {
            'who': 'self',
            'rate': Ticket.CORPORATE,
            'days': ['sat', 'sun', 'mon'],
            'company_name': 'Sirius Cybernetics Corp.',
            'company_addr': 'Eadrax, Sirius Tau',
            # The formset gets POSTed even when order is only for self
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': '',
            'form-1-email_addr': '',
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 1 ticket')

    def test_post_for_others(self):
        self.client.force_login(self.alice)
        form_data = {
            'who': 'others',
            'rate': Ticket.INDIVIDUAL,
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['mon', 'tue'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['sat', 'sun', 'mon'],
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 2 tickets')

    def test_post_for_self_and_others(self):
        self.client.force_login(self.alice)
        form_data = {
            'who': 'self and others',
            'rate': Ticket.INDIVIDUAL,
            'days': ['sat', 'sun', 'mon'],
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['mon', 'tue'],
            'form-1-email_addr': 'test2@example.com',
            'form-1-days': ['sat', 'sun', 'mon'],
        }
        rsp = self.client.post('/tickets/orders/new/', form_data, follow=True)
        self.assertContains(rsp, 'You are ordering 3 tickets')

    def test_get_when_not_authenticated(self):
        rsp = self.client.get('/tickets/orders/new/')
        self.assertInHTML('<tr><td class="text-center">5 days</td><td class="text-center">£198</td><td class="text-center">£396</td><td class="text-center">£66</td></tr>', rsp.content.decode())
        self.assertNotContains(rsp, '<form method="post" id="order-form">')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/tickets/orders/new/">sign up</a> or <a href="/accounts/login/?next=/tickets/orders/new/">sign in</a> to buy a ticket.', html=True)

    def test_post_when_not_authenticated(self):
        rsp = self.client.post('/tickets/orders/new/', follow=True)
        self.assertRedirects(rsp, '/accounts/login/')


class TicketTests(TestCase):
    def test_ticket(self):
        ticket = factories.create_ticket()
        self.client.force_login(ticket.owner)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/', follow=True)
        self.assertContains(rsp, f'Details of your ticket ({ticket.ticket_id})')
        self.assertContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Your profile is incomplete')
        self.assertContains(rsp, 'Update your profile')
        self.assertNotContains(rsp, 'Update your ticket')

    def test_incomplete_free_ticket(self):
        alice = factories.create_user('Alice')
        ticket = factories.create_claimed_free_ticket(alice)
        self.client.force_login(alice)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/', follow=True)
        self.assertRedirects(rsp, f'/tickets/tickets/{ticket.ticket_id}/edit/')

    def test_complete_free_ticket(self):
        alice = factories.create_user('Alice')
        ticket = factories.create_completed_free_ticket(alice)
        self.client.force_login(alice)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/', follow=True)
        self.assertNotContains(rsp, 'Cost (incl. VAT)')
        self.assertContains(rsp, 'Saturday, Sunday, Monday')
        self.assertContains(rsp, 'Update your ticket')

    def test_when_not_authenticated(self):
        ticket = factories.create_ticket()
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/tickets/tickets/{ticket.ticket_id}/')

    def test_when_not_authorized(self):
        ticket = factories.create_ticket()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a ticket can view the ticket')


class TicketEditTests(TestCase):
    def test_get_incomplete_free_ticket(self):
        alice = factories.create_user('Alice')
        ticket = factories.create_claimed_free_ticket(alice)
        self.client.force_login(alice)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertContains(rsp, 'Update my ticket')
        self.assertContains(rsp, '<input type="checkbox" name="days" value="sat">', html=True)

    def test_get_completed_free_ticket(self):
        alice = factories.create_user('Alice')
        ticket = factories.create_completed_free_ticket(alice)
        self.client.force_login(alice)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertContains(rsp, 'Update my ticket')
        self.assertContains(rsp, '<input type="checkbox" name="days" value="sat" checked>', html=True)

    def test_post(self):
        alice = factories.create_user('Alice')
        ticket = factories.create_completed_free_ticket(alice)
        self.client.force_login(alice)
        rsp = self.client.post(f'/tickets/tickets/{ticket.ticket_id}/edit/', {'days': ['sat', 'sun', 'mon', 'tue']}, follow=True)
        self.assertContains(rsp, 'Saturday, Sunday, Monday, Tuesday')
        self.assertContains(rsp, 'Update your ticket')

    def test_get_when_not_authenticated(self):
        ticket = factories.create_ticket()
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/tickets/tickets/{ticket.ticket_id}/edit/')

    def test_post_when_not_authenticated(self):
        ticket = factories.create_ticket()
        rsp = self.client.post(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next=/tickets/tickets/{ticket.ticket_id}/edit/')

    def test_get_when_not_authorized(self):
        ticket = factories.create_ticket()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a ticket can edit the ticket')

    def test_post_when_not_authorized(self):
        ticket = factories.create_ticket()
        bob = factories.create_user('Bob')
        self.client.force_login(bob)
        rsp = self.client.post(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'Only the owner of a ticket can edit the ticket')

    def test_get_when_not_editable(self):
        ticket = factories.create_ticket()
        self.client.force_login(ticket.owner)
        rsp = self.client.get(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/tickets/tickets/{ticket.ticket_id}/')
        self.assertContains(rsp, 'This ticket cannot be edited')

    def test_post_when_not_editable(self):
        ticket = factories.create_ticket()
        self.client.force_login(ticket.owner)
        rsp = self.client.post(f'/tickets/tickets/{ticket.ticket_id}/edit/', follow=True)
        self.assertRedirects(rsp, f'/tickets/tickets/{ticket.ticket_id}/')
        self.assertContains(rsp, 'This ticket cannot be edited')


class TicketInvitationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        factories.create_confirmed_order_for_others()
        cls.invitation = TicketInvitation.objects.get(email_addr='bob@example.com')
        cls.bob = factories.create_user('Bob')
        cls.url = f'/tickets/invitations/{cls.invitation.token}/'

    def test_for_unclaimed_invitation(self):
        self.client.force_login(self.bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, f'Details of your ticket ({self.invitation.ticket.ticket_id})')
        self.assertNotContains(rsp, 'This invitation has already been claimed', html=True)

    def test_for_claimed_invitation(self):
        self.client.force_login(factories.create_user('Carol'))
        actions.claim_ticket_invitation(self.bob, self.invitation)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, '<div class="alert alert-info" role="alert">This invitation has already been claimed</div>', html=True)

    def test_when_user_has_ticket(self):
        factories.create_ticket(self.bob)
        self.client.force_login(self.bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, '<div class="alert alert-danger" role="alert">You already have a ticket!  Please contact pyconuk-enquiries@python.org to arrange transfer of this invitaiton to somebody else.</div>', html=True)

    def test_when_not_authenticated(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, '<div class="alert alert-info" role="alert">You need to create an account to claim your invitation</div>', html=True)
        self.assertRedirects(rsp, f'/accounts/register/?next={self.url}')
