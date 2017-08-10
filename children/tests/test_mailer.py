import re

from django.core import mail
from django.test import TestCase

from . import factories

from children.mailer import send_order_confirmation_mail


class MailerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = factories.create_user(email_addr='alice@example.com')

    def test_send_order_confirmation_mail(self):
        order = factories.create_confirmed_order(self.alice)

        mail.outbox = []

        send_order_confirmation_mail(order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['alice@example.com'])
        self.assertEqual(email.from_email, 'PyCon UK 2017 <noreply@pyconuk.org>')
        self.assertEqual(email.subject, f"PyCon UK 2017 children's day order confirmation ({order.order_id})")
        self.assertTrue(re.search(r"You have purchased 1 ticket for the children's day at PyCon UK 2017", email.body))
        self.assertTrue(re.search(fr'http://testserver/children/orders/{order.order_id}/', email.body))
