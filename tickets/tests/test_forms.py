from django.http import QueryDict
from django.test import TestCase

from .utils import build_querydict

from tickets import forms


class TicketForOthersFormSetTests(TestCase):
    def test_is_valid_with_valid_data(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': 'test2@example.com', 
            'form-1-days': ['sat', 'sun', 'mon']
        })

        formset = forms.TicketForOthersFormSet(post_data)
        self.assertTrue(formset.is_valid())

    def test_is_valid_with_valid_data_and_empty_form(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': '', 
        })

        formset = forms.TicketForOthersFormSet(post_data)
        self.assertTrue(formset.is_valid())

    def test_is_not_valid_with_no_email_addr(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': '', 
            'form-1-days': ['sat', 'sun', 'mon']
        })

        formset = forms.TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{}, {'email_addr': ['This field is required.']}]
        )

    def test_is_not_valid_with_no_days(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': 'test2@example.com', 
        })

        formset = forms.TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{}, {'days': ['This field is required.']}]
        )

    def test_is_not_valid_with_no_nonempty_forms(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': '',
            'form-1-email_addr': '', 
        })

        formset = forms.TicketForOthersFormSet(post_data)
        self.assertEqual(
            formset.errors,
            [{'email_addr': ['This field is required.'], 'days': ['This field is required.']}, {}]
        )

    def test_email_addrs_and_days(self):
        post_data = build_querydict({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-email_addr': 'test1@example.com',
            'form-0-days': ['thu', 'fri'],
            'form-1-email_addr': 'test2@example.com', 
            'form-1-days': ['sat', 'sun', 'mon']
        })

        formset = forms.TicketForOthersFormSet(post_data)
        formset.errors  # Trigger full clean
        self.assertEqual(
            formset.email_addrs_and_days,
            [('test1@example.com', ['thu', 'fri']), ('test2@example.com', ['sat', 'sun', 'mon'])]
        )
