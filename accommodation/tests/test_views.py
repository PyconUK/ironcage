from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase
from django.utils.http import urlquote

from ironcage.tests import utils

from . import factories

from accommodation.models import ROOMS


class NewBookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def setUp(self):
        self.client.force_login(self.alice)

    def test_get_when_user_has_booking(self):
        factories.create_booking(self.alice)
        rsp = self.client.get('/accommodation/bookings/new/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'You have already booked a room')

    def test_get_when_some_rooms_available(self):
        factories.create_some_bookings()
        rsp = self.client.get('/accommodation/bookings/new/')
        self.assertContains(rsp, 'The following accommodation options are available')
        self.assertContains(rsp, ROOMS[0].description.replace("'", '&#39;'))
        self.assertNotContains(rsp, ROOMS[1].description.replace("'", '&#39;'))

    def test_get_when_no_rooms_available(self):
        factories.create_all_bookings()
        rsp = self.client.get('/accommodation/bookings/new/')
        self.assertNotContains(rsp, 'The following accommodation options are available')
        self.assertContains(rsp, 'There are currently no rooms available')

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get('/accommodation/bookings/new/')
        self.assertContains(rsp, 'The following accommodation options are available')
        self.assertNotContains(rsp, '<form')
        self.assertContains(rsp, 'Please <a href="/accounts/register/?next=/accommodation/bookings/new/">sign up</a> or <a href="/accounts/login/?next=/accommodation/bookings/new/">sign in</a> to book accommodation.', html=True)


class BookingPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user()

    def setUp(self):
        self.client.force_login(self.alice)
        self.url = f'/accommodation/bookings/payment/?room={ROOMS[1].key}'

    def test_get(self):
        rsp = self.client.get(self.url, follow=True)
        self.assertContains(rsp, 'Accommodation booking payment')
        self.assertContains(rsp, '<div id="stripe-form">')
        self.assertContains(rsp, f'data-amount="{ROOMS[1].cost_incl_vat * 100}"')
        self.assertContains(rsp, f'data-email="{self.alice.email_addr}"')

    def test_get_when_user_has_booking(self):
        factories.create_booking(self.alice)
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'You have already booked a room')

    def test_get_when_room_missing(self):
        rsp = self.client.get('/accommodation/bookings/payment/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'That room does not exist')

    def test_get_when_room_non_existent(self):
        rsp = self.client.get('/accommodation/bookings/payment/?rooms=xyz', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'That room does not exist')

    def test_get_when_room_booked(self):
        factories.create_some_bookings()
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, '/accommodation/bookings/new/')
        self.assertContains(rsp, f'{ROOMS[1].description} is sold out'.replace("'", '&#39;'))

    def test_get_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.get(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_post_when_user_has_booking(self):
        factories.create_booking(self.alice)
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'You have already booked a room')

    def test_post_when_room_missing(self):
        rsp = self.client.post('/accommodation/bookings/payment/', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'That room does not exist')

    def test_post_when_room_non_existent(self):
        rsp = self.client.post('/accommodation/bookings/payment/?rooms=xyz', follow=True)
        self.assertRedirects(rsp, '/')
        self.assertContains(rsp, 'That room does not exist')

    def test_post_when_room_booked(self):
        factories.create_some_bookings()
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, '/accommodation/bookings/new/')
        self.assertContains(rsp, f'{ROOMS[1].description} is sold out'.replace("'", '&#39;'))

    def test_post_when_not_authenticated(self):
        self.client.logout()
        rsp = self.client.post(self.url, follow=True)
        self.assertRedirects(rsp, f'/accounts/login/?next={urlquote(self.url)}')

    def test_post_stripe_success(self):
        with utils.patched_charge_creation_success():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this booking has been received')
        self.assertRedirects(rsp, '/')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.alice.email_addr])
        self.assertEqual(email.from_email, 'PyCon UK 2017 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, 'PyCon UK 2017 accommodation confirmation')
        self.assertIn(ROOMS[1].description, email.body)

        backend = get_slack_backend()
        messages = backend.retrieve_messages()
        self.assertEqual(len(messages), 1)
        text = messages[0]['text']
        self.assertIn(f'Alice has just booked themself into {ROOMS[1].description}'.replace("'", '&#39;'), text)

    def test_post_stripe_failure(self):
        with utils.patched_charge_creation_failure():
            rsp = self.client.post(
                self.url,
                {'stripeToken': 'tok_abcdefghijklmnopqurstuvwx'},
                follow=True,
            )
        self.assertContains(rsp, 'Payment for this booking failed (Your card was declined.)')
        self.assertRedirects(rsp, '/accommodation/bookings/new/')
