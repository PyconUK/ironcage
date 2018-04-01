from django.test import TestCase
from django.core.exceptions import ValidationError
from . import factories

from tickets.models import Ticket, TicketInvitation



# class OrderTests(TestCase):
#     def test_ticket_details_for_confirmed_order(self):
#         order = factories.create_confirmed_order_for_self_and_others()
#         ticket_ids = [t.ticket_id for t in order.all_tickets()]
#         expected_details = [{
#             'id': ticket_ids[0],
#             'name': 'Alice',
#             'days': 'Thursday, Friday, Saturday',
#             'cost_incl_vat': 126,
#             'cost_excl_vat': 105,
#         }, {
#             'id': ticket_ids[1],
#             'name': 'bob@example.com',
#             'days': 'Friday, Saturday',
#             'cost_incl_vat': 90,
#             'cost_excl_vat': 75,
#         }, {
#             'id': ticket_ids[2],
#             'name': 'carol@example.com',
#             'days': 'Saturday, Sunday',
#             'cost_incl_vat': 90,
#             'cost_excl_vat': 75,
#         }]
#         self.assertEqual(order.ticket_details(), expected_details)

#     def test_ticket_details_for_unconfirmed_order(self):
#         order = factories.create_unpaid_order_for_self_and_others()
#         expected_details = [{
#             'name': 'Alice',
#             'days': 'Thursday, Friday, Saturday',
#             'cost_incl_vat': 126,
#             'cost_excl_vat': 105,
#         }, {
#             'name': 'bob@example.com',
#             'days': 'Friday, Saturday',
#             'cost_incl_vat': 90,
#             'cost_excl_vat': 75,
#         }, {
#             'name': 'carol@example.com',
#             'days': 'Saturday, Sunday',
#             'cost_incl_vat': 90,
#             'cost_excl_vat': 75,
#         }]
#         self.assertEqual(order.ticket_details(), expected_details)

#     def test_ticket_summary(self):
#         order = factories.create_confirmed_order_for_self_and_others()
#         expected_summary = [{
#             'num_days': 2,
#             'num_tickets': 2,
#             'per_item_cost_excl_vat': 75,
#             'per_item_cost_incl_vat': 90,
#             'total_cost_excl_vat': 150,
#             'total_cost_incl_vat': 180,
#         }, {
#             'num_days': 3,
#             'num_tickets': 1,
#             'per_item_cost_excl_vat': 105,
#             'per_item_cost_incl_vat': 126,
#             'total_cost_excl_vat': 105,
#             'total_cost_incl_vat': 126,
#         }]
#         self.assertEqual(order.ticket_summary(), expected_summary)

#     def test_form_data_for_order_for_self(self):
#         order = factories.create_unpaid_order_for_self()
#         expected = {
#             'who': 'self',
#             'rate': 'individual',
#         }
#         self.assertEqual(order.form_data(), expected)

#     def test_form_data_for_order_for_others(self):
#         order = factories.create_unpaid_order_for_others()
#         expected = {
#             'who': 'others',
#             'rate': 'individual',
#         }
#         self.assertEqual(order.form_data(), expected)

#     def test_form_data_for_order_for_self_and_others(self):
#         order = factories.create_unpaid_order_for_self_and_others()
#         expected = {
#             'who': 'self and others',
#             'rate': 'individual',
#         }
#         self.assertEqual(order.form_data(), expected)

#     def test_self_form_data_for_order_for_self(self):
#         order = factories.create_unpaid_order_for_self()
#         expected = {
#             'days': ['thu', 'fri', 'sat'],
#         }
#         self.assertEqual(order.self_form_data(), expected)

#     def test_self_form_data_for_order_for_others(self):
#         order = factories.create_unpaid_order_for_others()
#         self.assertEqual(order.self_form_data(), None)

#     def test_self_form_data_for_order_for_self_and_others(self):
#         order = factories.create_unpaid_order_for_self_and_others()
#         expected = {
#             'days': ['thu', 'fri', 'sat'],
#         }
#         self.assertEqual(order.self_form_data(), expected)

#     def test_others_formset_data_for_order_for_self(self):
#         order = factories.create_unpaid_order_for_self()
#         self.assertEqual(order.others_formset_data(), None)

#     def test_others_formset_data_for_order_for_others(self):
#         order = factories.create_unpaid_order_for_others()
#         expected = {
#             'form-TOTAL_FORMS': '2',
#             'form-INITIAL_FORMS': '2',
#             'form-0-days': ['fri', 'sat'],
#             'form-0-email_addr': 'bob@example.com',
#             'form-1-days': ['sat', 'sun'],
#             'form-1-email_addr': 'carol@example.com',
#         }
#         self.assertEqual(order.others_formset_data(), expected)

#     def test_others_formset_data_for_order_for_self_and_others(self):
#         order = factories.create_unpaid_order_for_self_and_others()
#         expected = {
#             'form-TOTAL_FORMS': '2',
#             'form-INITIAL_FORMS': '2',
#             'form-0-days': ['fri', 'sat'],
#             'form-0-email_addr': 'bob@example.com',
#             'form-1-days': ['sat', 'sun'],
#             'form-1-email_addr': 'carol@example.com',
#         }
#         self.assertEqual(order.others_formset_data(), expected)

#     def test_company_details_form_data_for_individual_order(self):
#         order = factories.create_unpaid_order_for_self()
#         self.assertEqual(order.company_details_form_data(), None)

#     def test_company_details_form_data_for_corporate_order(self):
#         order = factories.create_unpaid_order_for_self(rate='corporate')
#         expected = {
#             'company_name': 'Sirius Cybernetics Corp.',
#             'company_addr': 'Eadrax, Sirius Tau',
#         }
#         self.assertEqual(order.company_details_form_data(), expected)

#     def test_ticket_for_self_for_order_for_self(self):
#         order = factories.create_confirmed_order_for_self()
#         self.assertIsNotNone(order.ticket_for_self())

#     def test_ticket_for_self_for_order_for_self_and_others(self):
#         order = factories.create_confirmed_order_for_self_and_others()
#         self.assertIsNotNone(order.ticket_for_self())

#     def test_ticket_for_self_for_order_for_others(self):
#         order = factories.create_confirmed_order_for_others()
#         self.assertIsNone(order.ticket_for_self())

#     def test_tickets_for_others_for_order_for_self(self):
#         order = factories.create_confirmed_order_for_self()
#         self.assertEqual(len(order.tickets_for_others()), 0)

#     def test_tickets_for_others_for_order_for_self_and_others(self):
#         order = factories.create_confirmed_order_for_self_and_others()
#         self.assertEqual(len(order.tickets_for_others()), 2)

#     def test_tickets_for_others_for_order_for_others(self):
#         order = factories.create_confirmed_order_for_others()
#         self.assertEqual(len(order.tickets_for_others()), 2)

#     def test_company_addr_formatted(self):
#         order = factories.create_unpaid_order_for_self(rate='corporate')
#         order.company_addr = '''
# City Hall,
# Cathays Park
# Cardiff
# '''.strip()
#         self.assertEqual(order.company_addr_formatted(), 'City Hall, Cathays Park, Cardiff')
