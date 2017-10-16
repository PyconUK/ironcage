from django.test import TestCase
from django.utils.http import urlquote

from ironcage.tests import utils

from . import factories

from dinners.menus import MENUS


class ContributorsDinnerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(is_contributor=True)

    def setUp(self):
        self.client.force_login(self.alice)
        self.url = '/dinners/contributors-dinner/'

    def test_get_when_not_logged_in(self):
        self.client.logout()
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_get_when_not_contributor(self):
        bob = factories.create_user(is_contributor=False)
        self.client.force_login(bob)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/')

    def test_get_when_already_made_booking(self):
        factories.create_contributors_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, "You're coming to the contributors' dinner on Sunday at the Clink.")

    def test_get_when_not_already_made_booking(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'As a contributor to the conference')

    def test_get_when_not_already_made_booking_and_conference_dinner_sold_out(self):
        factories.create_all_bookings('conference')
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, "As a contributor to the conference, we'd like to invite you to the contributors' dinner")
        self.assertNotContains(rsp, 'Choose your dinner')
        self.assertNotContains(rsp, MENUS['conference']['main'][0][1])
        self.assertContains(rsp, MENUS['contributors']['main'][0][1])

    def test_get_when_not_already_made_booking_and_contributors_dinner_sold_out(self):
        factories.create_all_bookings('contributors')
        rsp = self.client.get(self.url, follow=True)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, "As a contributor to the conference, we'd like to invite you to the conference dinner")
        self.assertNotContains(rsp, 'Choose your dinner')
        self.assertContains(rsp, MENUS['conference']['main'][0][1])
        self.assertNotContains(rsp, MENUS['contributors']['main'][0][1])

    def test_get_when_not_already_made_booking_and_both_dinners_sold_out(self):
        factories.create_all_bookings('conference')
        factories.create_all_bookings('contributors')
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'Unfortunately, there are no tickets left')
        self.assertNotContains(rsp, MENUS['contributors']['main'][0][1])
        self.assertNotContains(rsp, MENUS['contributors']['main'][0][1])

    def test_post_when_not_logged_in(self):
        self.client.logout()
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_post_when_not_contributor(self):
        bob = factories.create_user(is_contributor=False)
        self.client.force_login(bob)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, f'/')

    def test_post_when_already_made_booking(self):
        factories.create_contributors_booking(self.alice)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, self.url)

    def test_post_when_not_already_made_booking(self):
        data = {
            'which_dinner': 'contributors',
            'starter': 'soup',
            'main': 'risotto',
            'pudding': 'cheesecake',
        }
        rsp = self.client.post(self.url, data, follow=True)
        self.assertContains(rsp, "You're coming to the contributors' dinner on Sunday at the Clink.")
        self.assertContains(rsp, 'Starter: Soup of the Day')
        self.assertContains(rsp, 'Main: Broad bean risotto')
        self.assertContains(rsp, 'Pudding: Dark chocolate and cardamom cheesecake')
        self.assertRedirects(rsp, self.url)

    def test_post_when_no_seats_available(self):
        factories.create_all_bookings('contributors')
        data = {
            'which_dinner': 'contributors',
            'starter': 'soup',
            'main': 'risotto',
            'pudding': 'cheesecake',
        }
        rsp = self.client.post(self.url, data, follow=True)
        self.assertContains(rsp, 'Sorry, there are now no seats left for that dinner')
        self.assertRedirects(rsp, self.url)


class ConferenceDinnerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(is_contributor=True)

    def setUp(self):
        self.client.force_login(self.alice)
        self.url = '/dinners/conference-dinner/'

    def test_get_when_not_logged_in(self):
        self.client.logout()
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_get_when_contributer_not_booked_for_any_dinner(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/dinners/contributors-dinner/')
        self.assertContains(rsp, 'Tickets to the conference dinner cost &pound;30')

    def test_get_when_contributer_booked_for_contributors_dinner(self):
        factories.create_contributors_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'Place your order below')
        self.assertContains(rsp, '<form action="/dinners/conference-dinner/payment/')

    def test_get_when_contributer_booked_for_conference_dinner(self):
        factories.create_contributors_booking(self.alice, venue='conference')
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, "You're coming to the conference dinner on Friday at City Hall")

    def test_get_when_contributor_booked_for_both_dinners(self):
        factories.create_contributors_booking(self.alice, venue='conference')
        factories.create_paid_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, "You're coming to the conference dinner on Friday at City Hall")

    def test_get_when_sold_out(self):
        factories.create_all_bookings('conference')
        factories.create_contributors_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'Unfortunately, there are no tickets left')
        self.assertNotContains(rsp, MENUS['conference']['main'][0][1])


class ConferenceDinnerPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def setUp(self):
        self.client.force_login(self.alice)
        self.url = '/dinners/conference-dinner/payment/?starter=tomato-soup&main=lamb&pudding=tart'

    def test_get_when_not_logged_in(self):
        self.client.logout()
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_get_when_already_booked(self):
        factories.create_paid_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/dinners/conference-dinner/')
        self.assertContains(rsp, 'You have already booked for the conference dinner')

    def test_get_when_not_already_booked(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, f'data-amount="3000"')
        self.assertContains(rsp, f'data-email="{self.alice.email_addr}"')

    def test_get_when_sold_out(self):
        factories.create_all_bookings('conference')
        factories.create_contributors_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'Unfortunately, there are no tickets left')
        self.assertContains(rsp, 'Sorry, there are now no seats left for the conference dinner')
        self.assertNotContains(rsp, MENUS['conference']['main'][0][1])

    def test_post_when_not_logged_in(self):
        self.client.logout()
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_post_when_already_booked(self):
        factories.create_paid_booking(self.alice)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, f'/dinners/conference-dinner/')
        self.assertContains(rsp, 'You have already booked for the conference dinner')

    def test_post_stripe_success(self):
        with utils.patched_charge_creation_success():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment succeeded')
        self.assertRedirects(rsp, '/dinners/conference-dinner/')

    def test_post_stripe_failure(self):
        with utils.patched_charge_creation_failure():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment failed (Your card was declined.)')
        self.assertRedirects(rsp, '/dinners/conference-dinner/')

    def test_post_when_sold_out(self):
        factories.create_all_bookings('conference')
        factories.create_contributors_booking(self.alice)
        rsp = self.client.post(self.url, follow=True)
        self.assertContains(rsp, 'Unfortunately, there are no tickets left')
        self.assertContains(rsp, 'Sorry, there are now no seats left for the conference dinner')
        self.assertNotContains(rsp, MENUS['conference']['main'][0][1])
