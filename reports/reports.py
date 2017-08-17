from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.generic import TemplateView
from avatar.templatetags.avatar_tags import avatar_url

from accounts.models import User
from cfp.models import Proposal
from tickets.constants import DAYS
from tickets.models import Order, Ticket
from tickets.prices import cost_incl_vat
from ukpa.models import Nomination


@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ReportView(TemplateView):
    template_name = 'reports/report.html'

    def get_context_data(self):
        return {
            'title': self.title,
            'headings': self.headings,
            'rows': [self.presenter(item) for item in self.get_queryset()],
        }

    @classmethod
    def path(cls):
        return f'^{slugify(cls.title)}/$'

    @classmethod
    def url_name(cls):
        return slugify(cls.title)

    @classmethod
    def namespaced_url_name(cls):
        return f'reports:{cls.url_name()}'


class AttendanceByDayReport(ReportView):
    title = 'Attendance by day'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        rows = []

        for day in DAYS:
            num_tickets = {
                'individual': 0,
                'corporate': 0,
                'education': 0,
            }

            for ticket in tickets:
                if getattr(ticket, day):
                    num_tickets[ticket.order.rate] += 1

            rows.append([
                DAYS[day],
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'],
            ])

        return {
            'title': self.title,
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Education rate', 'Total'],
            'rows': rows,
        }


class UKPAReport(ReportView):
    title = 'UKPA Membership'

    def get_context_data(self):
        members = User.objects.filter(is_ukpa_member=True)
        rows = [[member.name, member.email_addr] for member in members]

        return {
            'title': self.title,
            'headings': ['Name', 'email'],
            'rows': rows,
        }


class CandidateReport(ReportView):
    title = 'Candidates for UKPA Trustee Election'

    def get_context_data(self):
        candidates = Nomination.objects.all()
        rows = [
            [
                candidate.nominee.name,
                candidate.statement,
                avatar_url(candidate.nominee)
            ]
            for candidate in candidates
        ]

        return {
            'title': self.title,
            'headings': ['Name', 'Statement', 'Avatar URL'],
            'rows': rows,
        }


class TicketSalesReport(ReportView):
    title = 'Ticket sales'
    template_name = 'reports/ticket_sales_report.html'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        num_tickets_rows = []
        ticket_cost_rows = []

        for ix in range(5):
            num_days = ix + 1
            individual_rate = cost_incl_vat('individual', num_days)
            corporate_rate = cost_incl_vat('corporate', num_days)
            education_rate = cost_incl_vat('education', num_days)

            num_tickets = {
                'individual': 0,
                'corporate': 0,
                'education': 0,
            }

            for ticket in tickets:
                if sum(getattr(ticket, day) for day in DAYS) == num_days:
                    num_tickets[ticket.order.rate] += 1

            num_tickets_rows.append([
                num_days,
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'],
            ])

            ticket_cost_rows.append([
                num_days,
                f'£{num_tickets["individual"] * individual_rate}',
                f'£{num_tickets["corporate"] * corporate_rate}',
                f'£{num_tickets["education"] * education_rate}',
                f'£{num_tickets["individual"] * individual_rate + num_tickets["corporate"] * corporate_rate + num_tickets["education"] * education_rate}',
            ])

        return {
            'title': self.title,
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Education rate', 'Total'],
            'num_tickets_rows': num_tickets_rows,
            'ticket_cost_rows': ticket_cost_rows,
        }


class OrdersMixin:
    headings = ['ID', 'Rate', 'Purchaser', 'Email', 'Tickets', 'Cost (incl. VAT)', 'Status']

    def presenter(self, order):
        link = {
            'href': reverse('reports:tickets_order', args=[order.order_id]),
            'text': order.order_id,
        }
        return [
            link,
            order.rate,
            order.purchaser.name,
            order.purchaser.email_addr,
            order.num_tickets(),
            f'£{order.cost_incl_vat()}',
            order.status,
        ]


class OrdersReport(ReportView, OrdersMixin):
    title = 'All orders'

    def get_queryset(self):
        return Order.objects.all()


class UnpaidOrdersReport(ReportView, OrdersMixin):
    title = 'Unpaid orders'

    def get_queryset(self):
        return Order.objects.exclude(status='successful')


class TicketsMixin:
    headings = ['ID', 'Rate', 'Ticket holder', 'Days', 'Cost (incl. VAT)', 'Status']

    def presenter(self, ticket):
        link = {
            'href': reverse('reports:tickets_ticket', args=[ticket.ticket_id]),
            'text': ticket.ticket_id,
        }
        return [
            link,
            ticket.order.rate,
            ticket.ticket_holder_name(),
            ', '.join(ticket.days()),
            f'£{ticket.cost_incl_vat()}',
            'Assigned' if ticket.owner else 'Unclaimed',
        ]


class TicketsReport(ReportView, TicketsMixin):
    title = 'All tickets'

    def get_queryset(self):
        return Ticket.objects.all()


class UnclaimedTicketsReport(ReportView, TicketsMixin):
    title = 'Unclaimed tickets'

    def get_queryset(self):
        return Ticket.objects.filter(owner=None)


class CFPPropsalsMixin:
    headings = [
        'ID',
        'Title',
        'Type',
        'Proposer',
        'State',
        'Track',
        'New programmers?',
        'Mentor?',
        'Amount requested',
    ]

    def presenter(self, proposal):
        link = {
            'href': reverse('reports:cfp_proposal', args=[proposal.proposal_id]),
            'text': proposal.proposal_id,
        }

        grant_appliction = proposal.proposer.get_grant_application()
        if grant_appliction is None:
            amount_requested = ''
        else:
            amount_requested = grant_appliction.amount_requested

        return [
            link,
            proposal.full_title(),
            proposal.session_type,
            proposal.proposer.name,
            proposal.state,
            proposal.track,
            '✔' if proposal.aimed_at_new_programmers else '✘',
            '✔' if proposal.would_like_mentor else '✘',
            amount_requested,
        ]


class CFPPropsals(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').all()


class CFPPropsalsPlanToAccept(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals we plan to accept'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='plan to accept')


class CFPPropsalsPlanToReject(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals we plan to reject'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='plan to reject')


class CFPPropsalsNoDecision(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals we with no decision'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='')


class CFPPropsalsAimedAtNewProgrammers(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals aimed at new programmers'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(aimed_at_new_programmers=True)


class CFPPropsalsAimedAtTeachers(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals aimed at teachers'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(aimed_at_teachers=True)


class CFPPropsalsAimedAtDataScientists(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals aimed at data scientists'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(aimed_at_data_scientists=True)


class SpeakersSeekingMentorReport(ReportView):
    title = 'Speakers Seeking Mentors'

    headings = [
        'Speaker',
        'Title'
    ]

    def get_queryset(self):
        return Proposal.objects.filter(would_like_mentor=True)

    def presenter(self, proposal):
        return [proposal.proposer.name, proposal.title]


class AttendeesWithAccessibilityReqs(ReportView):
    title = 'Attendees with accessibility requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(accessibility_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.accessibility_reqs]


class AttendeesWithChildcareReqs(ReportView):
    title = 'Attendees with childcare requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(childcare_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.childcare_reqs]


class AttendeesWithDietaryReqs(ReportView):
    title = 'Attendees with dietary requirements'

    headings = [
        'Name',
        'Email',
        'Requirements',
    ]

    def get_queryset(self):
        return User.objects.filter(dietary_reqs_yn=True)

    def presenter(self, user):
        return [user.name, user.email_addr, user.dietary_reqs]


reports = [
    AttendanceByDayReport,
    UKPAReport,
    CandidateReport,
    TicketSalesReport,
    OrdersReport,
    UnpaidOrdersReport,
    TicketsReport,
    UnclaimedTicketsReport,
    CFPPropsals,
    CFPPropsalsPlanToAccept,
    CFPPropsalsPlanToReject,
    CFPPropsalsNoDecision,
    CFPPropsalsAimedAtNewProgrammers,
    CFPPropsalsAimedAtTeachers,
    CFPPropsalsAimedAtDataScientists,
    SpeakersSeekingMentorReport,
    AttendeesWithAccessibilityReqs,
    AttendeesWithChildcareReqs,
    AttendeesWithDietaryReqs,
]
