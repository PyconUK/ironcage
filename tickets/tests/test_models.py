from django.test import TestCase

from . import factories


class OrderTests(TestCase):
    def test_cost_incl_vat_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(order.cost_incl_vat(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_cost_incl_vat_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        self.assertEqual(order.cost_incl_vat(), 222)  # 222 == 3 * 18 + 7 * 24

    def test_cost_excl_vat_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(order.cost_excl_vat(), 185)  # 185 == 3 * 15 + 7 * 20

    def test_cost_excl_vat_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        self.assertEqual(order.cost_excl_vat(), 185)  # 185 == 3 * 15 + 7 * 20

    def test_ticket_details_for_confirmed_order(self):
        order = factories.create_confirmed_order_for_self_and_others()
        ticket_ids = [t.ticket_id for t in order.all_tickets()]
        expected_details = [{
            'id': ticket_ids[0],
            'name': 'Alice',
            'days': 'Thursday, Friday, Saturday',
            'cost_incl_vat': 90,
            'cost_excl_vat': 75,
        }, {
            'id': ticket_ids[1],
            'name': 'bob@example.com',
            'days': 'Friday, Saturday',
            'cost_incl_vat': 66,
            'cost_excl_vat': 55,
        }, {
            'id': ticket_ids[2],
            'name': 'carol@example.com',
            'days': 'Saturday, Sunday',
            'cost_incl_vat': 66,
            'cost_excl_vat': 55,
        }]
        self.assertEqual(order.ticket_details(), expected_details)

    def test_ticket_details_for_unconfirmed_order(self):
        order = factories.create_pending_order_for_self_and_others()
        expected_details = [{
            'name': 'Alice',
            'days': 'Thursday, Friday, Saturday',
            'cost_incl_vat': 90,
            'cost_excl_vat': 75,
        }, {
            'name': 'bob@example.com',
            'days': 'Friday, Saturday',
            'cost_incl_vat': 66,
            'cost_excl_vat': 55,
        }, {
            'name': 'carol@example.com',
            'days': 'Saturday, Sunday',
            'cost_incl_vat': 66,
            'cost_excl_vat': 55,
        }]
        self.assertEqual(order.ticket_details(), expected_details)

    def test_ticket_summary(self):
        order = factories.create_confirmed_order_for_self_and_others()
        expected_summary = [{
            'num_days': 2,
            'num_tickets': 2,
            'per_item_cost_excl_vat': 55,
            'per_item_cost_incl_vat': 66,
            'total_cost_excl_vat': 110,
            'total_cost_incl_vat': 132,
        }, {
            'num_days': 3,
            'num_tickets': 1,
            'per_item_cost_excl_vat': 75,
            'per_item_cost_incl_vat': 90,
            'total_cost_excl_vat': 75,
            'total_cost_incl_vat': 90,
        }]
        self.assertEqual(order.ticket_summary(), expected_summary)

    def test_form_data_for_order_for_self(self):
        order = factories.create_pending_order_for_self()
        expected = {
            'who': 'self',
            'rate': 'individual',
        }
        self.assertEqual(order.form_data(), expected)

    def test_form_data_for_order_for_others(self):
        order = factories.create_pending_order_for_others()
        expected = {
            'who': 'others',
            'rate': 'individual',
        }
        self.assertEqual(order.form_data(), expected)

    def test_form_data_for_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'who': 'self and others',
            'rate': 'individual',
        }
        self.assertEqual(order.form_data(), expected)

    def test_self_form_data_for_order_for_self(self):
        order = factories.create_pending_order_for_self()
        expected = {
            'days': ['thu', 'fri', 'sat'],
        }
        self.assertEqual(order.self_form_data(), expected)

    def test_self_form_data_for_order_for_others(self):
        order = factories.create_pending_order_for_others()
        self.assertEqual(order.self_form_data(), None)

    def test_self_form_data_for_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'days': ['thu', 'fri', 'sat'],
        }
        self.assertEqual(order.self_form_data(), expected)

    def test_others_formset_data_for_order_for_self(self):
        order = factories.create_pending_order_for_self()
        self.assertEqual(order.others_formset_data(), None)

    def test_others_formset_data_for_order_for_others(self):
        order = factories.create_pending_order_for_others()
        expected = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-0-days': ['fri', 'sat'],
            'form-0-email_addr': 'bob@example.com',
            'form-1-days': ['sat', 'sun'],
            'form-1-email_addr': 'carol@example.com',
        }
        self.assertEqual(order.others_formset_data(), expected)

    def test_others_formset_data_for_order_for_self_and_others(self):
        order = factories.create_pending_order_for_self_and_others()
        expected = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-0-days': ['fri', 'sat'],
            'form-0-email_addr': 'bob@example.com',
            'form-1-days': ['sat', 'sun'],
            'form-1-email_addr': 'carol@example.com',
        }
        self.assertEqual(order.others_formset_data(), expected)

    def test_ticket_for_self_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self()
        self.assertIsNotNone(order.ticket_for_self())

    def test_ticket_for_self_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertIsNotNone(order.ticket_for_self())

    def test_ticket_for_self_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others()
        self.assertIsNone(order.ticket_for_self())

    def test_tickets_for_others_for_order_for_self(self):
        order = factories.create_confirmed_order_for_self()
        self.assertEqual(len(order.tickets_for_others()), 0)

    def test_tickets_for_others_for_order_for_self_and_others(self):
        order = factories.create_confirmed_order_for_self_and_others()
        self.assertEqual(len(order.tickets_for_others()), 2)

    def test_tickets_for_others_for_order_for_others(self):
        order = factories.create_confirmed_order_for_others()
        self.assertEqual(len(order.tickets_for_others()), 2)
