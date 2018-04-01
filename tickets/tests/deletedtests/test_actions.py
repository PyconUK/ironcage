from django_slack.utils import get_backend as get_slack_backend

from django.core import mail
from django.test import TestCase

from . import factories
from ironcage.tests import utils

from tickets import actions
from tickets.models import TicketInvitation, Ticket
from payments import actions as payment_actions
from payments.models import Payment

# class UpdatePendingOrderTests(TestCase):
#     def test_order_for_self_to_order_for_self(self):
#         order = factories.create_pending_order_for_self()
#         actions.update_pending_order(
#             order,
#             Ticket.INDIVIDUAL,
#             days_for_self=['sat'],
#         )

#         self.assertEqual(order.status, 'pending')
#         self.assertEqual(order.rate, Ticket.INDIVIDUAL)
#         self.assertEqual(
#             order.ticket_details(),
#             [{'name': 'Alice', 'days': 'Saturday', 'cost_incl_vat': 54, 'cost_excl_vat': 45}]
#         )

#     def test_order_for_self_to_order_for_others(self):
#         order = factories.create_pending_order_for_self()
#         actions.update_pending_order(
#             order,
#             Ticket.INDIVIDUAL,
#             email_addrs_and_days_for_others=[
#                 ('bob@example.com', ['sat', 'sun']),
#                 ('carol@example.com', ['sun', 'mon']),
#             ]
#         )

#         self.assertEqual(order.status, 'pending')
#         self.assertEqual(order.rate, Ticket.INDIVIDUAL)
#         self.assertEqual(
#             order.ticket_details(),
#             [
#                 {'name': 'bob@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
#                 {'name': 'carol@example.com', 'days': 'Sunday, Monday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
#             ]
#         )

#     def test_order_for_self_to_order_for_self_and_others(self):
#         order = factories.create_pending_order_for_self()
#         actions.update_pending_order(
#             order,
#             Ticket.INDIVIDUAL,
#             days_for_self=['sat', 'sun', 'mon'],
#             email_addrs_and_days_for_others=[
#                 ('bob@example.com', ['sat', 'sun']),
#                 ('carol@example.com', ['sun', 'mon']),
#             ]
#         )

#         self.assertEqual(order.status, 'pending')
#         self.assertEqual(order.rate, Ticket.INDIVIDUAL)
#         self.assertEqual(
#             order.ticket_details(),
#             [
#                 {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
#                 {'name': 'bob@example.com', 'days': 'Saturday, Sunday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
#                 {'name': 'carol@example.com', 'days': 'Sunday, Monday', 'cost_incl_vat': 90, 'cost_excl_vat': 75},
#             ]
#         )

#     def test_individual_order_to_corporate_order(self):
#         order = factories.create_pending_order_for_self()
#         actions.update_pending_order(
#             order,
#             Ticket.CORPORATE,
#             days_for_self=['sat', 'sun', 'mon'],
#             company_details={
#                 'name': 'Sirius Cybernetics Corp.',
#                 'addr': 'Eadrax, Sirius Tau',
#             },
#         )

#         self.assertEqual(order.status, 'pending')
#         self.assertEqual(order.rate, Ticket.CORPORATE)
#         self.assertEqual(order.company_name, 'Sirius Cybernetics Corp.')
#         self.assertEqual(order.company_addr, 'Eadrax, Sirius Tau')
#         self.assertEqual(
#             order.ticket_details(),
#             [
#                 {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 252, 'cost_excl_vat': 210},
#             ]
#         )

#     def test_corporate_order_to_individual_order(self):
#         order = factories.create_pending_order_for_self(rate=Ticket.CORPORATE)
#         actions.update_pending_order(
#             order,
#             Ticket.INDIVIDUAL,
#             days_for_self=['sat', 'sun', 'mon'],
#         )

#         self.assertEqual(order.status, 'pending')
#         self.assertEqual(order.rate, Ticket.INDIVIDUAL)
#         self.assertEqual(order.company_name, None)
#         self.assertEqual(order.company_addr, None)
#         self.assertEqual(
#             order.ticket_details(),
#             [
#                 {'name': 'Alice', 'days': 'Saturday, Sunday, Monday', 'cost_incl_vat': 126, 'cost_excl_vat': 105},
#             ]
#         )
