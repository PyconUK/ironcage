from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, IntegerField, Sum, Value
from django.db.models.expressions import Case, When
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.generic import TemplateView
from avatar.templatetags.avatar_tags import avatar_url

from accommodation.models import Booking as AccommodationBooking
from accounts.models import User
from cfp.models import Proposal
from children.models import Ticket as ChildTicket
from dinners.models import Booking as DinnerBooking
from grants.models import Application
from tickets.constants import DAYS
from tickets.models import Order, Ticket
from tickets.prices import PRICES_EXCL_VAT, cost_incl_vat
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


class TicketSummaryReport(ReportView):
    title = 'Ticket summary'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        rows = [
            ['Tickets', len(tickets)],
            ['Days', sum(t.num_days() for t in tickets)],
            ['Cost (excl. VAT)', f'£{sum(t.cost_excl_vat() for t in tickets)}'],
        ]

        return {
            'title': self.title,
            'rows': rows,
            'headings': [],
        }


class AttendanceByDayReport(ReportView):
    title = 'Attendance by day'

    def get_context_data(self):
        tickets = Ticket.objects.all()

        rows = []

        for day in DAYS:
            num_tickets = {rate: 0 for rate in PRICES_EXCL_VAT}

            for ticket in tickets:
                if getattr(ticket, day):
                    num_tickets[ticket.rate()] += 1

            rows.append([
                DAYS[day],
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['free'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'] + num_tickets['free'],
            ])

        return {
            'title': self.title,
            'headings': ['Day', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
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

            num_tickets = {rate: 0 for rate in PRICES_EXCL_VAT}

            for ticket in tickets:
                if sum(getattr(ticket, day) for day in DAYS) == num_days:
                    num_tickets[ticket.rate()] += 1

            num_tickets_rows.append([
                num_days,
                num_tickets['individual'],
                num_tickets['corporate'],
                num_tickets['education'],
                num_tickets['free'],
                num_tickets['individual'] + num_tickets['corporate'] + num_tickets['education'] + num_tickets['free'],
            ])

            ticket_cost_rows.append([
                num_days,
                f'£{num_tickets["individual"] * individual_rate}',
                f'£{num_tickets["corporate"] * corporate_rate}',
                f'£{num_tickets["education"] * education_rate}',
                f'£0',
                f'£{num_tickets["individual"] * individual_rate + num_tickets["corporate"] * corporate_rate + num_tickets["education"] * education_rate}',
            ])

        return {
            'title': self.title,
            'headings': ['Days', 'Individual rate', 'Corporate rate', 'Education rate', 'Free', 'Total'],
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
            ticket.rate(),
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
        return Ticket.objects.filter(owner=None).order_by('id')


class FreeTicketsReport(ReportView):
    title = 'Free tickets'
    headings = ['ID', 'Ticket holder', 'Days', 'Pot', 'Status']

    def get_queryset(self,):
        return Ticket.objects.filter(pot__isnull=False).order_by('pot')

    def presenter(self, ticket):
        link = {
            'href': reverse('reports:tickets_ticket', args=[ticket.ticket_id]),
            'text': ticket.ticket_id,
        }
        return [
            link,
            ticket.ticket_holder_name(),
            ', '.join(ticket.days()),
            ticket.pot,
            'Assigned' if ticket.owner else 'Unclaimed',
        ]


class DjangoGirlsTicketsReport(ReportView):
    title = 'Django Girls tickets'
    headings = ['ID', 'Ticket holder', 'Days', 'Status']

    def get_queryset(self,):
        return Ticket.objects.filter(pot='Django Girls').order_by('id')

    def presenter(self, ticket):
        link = {
            'href': reverse('reports:tickets_ticket', args=[ticket.ticket_id]),
            'text': ticket.ticket_id,
        }
        return [
            link,
            ticket.ticket_holder_name(),
            ', '.join(ticket.days()),
            'Assigned' if ticket.owner else 'Unclaimed',
        ]


class ChildrensDayTicketsReport(ReportView):
    title = "Children's day tickets"
    headings = [
        'ID',
        'Name',
        'Adult name',
        'Adult email address',
        'Adult phone number',
    ]

    def presenter(self, ticket):
        return [
            ticket.ticket_id,
            ticket.name,
            ticket.order.adult_name,
            ticket.order.adult_email_addr,
            ticket.order.adult_phone_number,
        ]

    def get_queryset(self):
        return ChildTicket.objects.order_by('name')


class ChildrensDaySummaryReport(ReportView):
    title = "Children's day summary"

    def get_context_data(self):
        rows = [
            ['Tickets', ChildTicket.objects.count()],
        ]

        return {
            'title': self.title,
            'rows': rows,
            'headings': [],
        }


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
        'Special reply required',
        'Room',
        'Time',
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
            '✔' if proposal.special_reply_required else '✘',
            proposal.scheduled_room,
            proposal.scheduled_time,
        ]


class CFPPropsals(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').all()


class CFPPropsalsForEducationTrack(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals to be scheduled in education track'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='accepted', track='education')


class CFPPropsalsPlanToAccept(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals we accepted'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='accepted')


class CFPPropsalsPlanToAcceptOfTypeOther(ReportView, CFPPropsalsMixin):
    title = 'CFP Proposals we accepted with type "other"'

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='accepted', session_type='other')


class CFPPropsalsPlanToAcceptWithGrantApplications(ReportView, CFPPropsalsMixin):
    title = "CFP Proposals we accepted from people who've applied for a grant"

    def get_queryset(self):
        return Proposal.objects.select_related('proposer', 'proposer__grant_application').filter(state='accepted', proposer__grant_application__isnull=False).order_by('proposer__grant_application__amount_requested')


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


class GrantApplicationsMixin:
    headings = [
        'ID',
        'Name',
        'Amount requested',
        'Amount offered',
        'Requested ticket only',
        'Special reply required',
    ]

    def presenter(self, application):
        link = {
            'href': reverse('reports:grants_application', args=[application.application_id]),
            'text': application.application_id,
        }

        return [
            link,
            application.applicant.name,
            application.amount_requested,
            application.amount_offered,
            '✔' if application.requested_ticket_only else '✘',
            '✔' if application.special_reply_required else '✘',
        ]


class GrantApplications(ReportView, GrantApplicationsMixin):
    title = 'Grant applications'

    def get_queryset(self):
        return Application.objects.select_related('applicant').order_by('amount_requested').all()


class GrantApplicationsWithFundsOffered(ReportView, GrantApplicationsMixin):
    title = 'Grant applications with funds offered'

    def get_queryset(self):
        return Application.objects.filter(amount_offered__gt=0).select_related('applicant').order_by('amount_offered').all()


class PeopleMixin:
    headings = ['ID', 'Name', 'Email address']

    def presenter(self, user):
        link = {
            'href': reverse('reports:accounts_user', args=[user.user_id]),
            'text': user.user_id,
        }

        return [
            link,
            user.name,
            user.email_addr,
        ]


class PeopleReport(ReportView, PeopleMixin):
    title = 'People'

    def get_queryset(self):
        return User.objects.order_by('name').all()


class ContributorReport(ReportView, PeopleMixin):
    title = 'Contributors'

    def get_queryset(self):
        return User.objects.filter(is_contributor=True).order_by('name')


class TicketHoldersWithIncompleteNameReport(ReportView, PeopleMixin):
    title = 'Ticket holders with incomplete name'

    def get_queryset(self):
        return User.objects.filter(ticket__isnull=False).exclude(name__contains=' ')


class AccommodationReport(ReportView):
    title = 'Accommodation booked'
    headings = []

    def get_queryset(self):
        return User.objects.filter(ticket__isnull=False).values('has_booked_hotel').annotate(Count('has_booked_hotel'))

    def presenter(self, result):
        return [
            result['has_booked_hotel'],
            result['has_booked_hotel__count'],
        ]


class AccommodationBookingsReport(ReportView):
    title = 'Accommodation booked through us'
    headings = ['Room', 'Name', 'Email address']

    def get_queryset(self):
        return AccommodationBooking.objects.order_by('room_key')

    def presenter(self, booking):
        return [
            booking.room_description(),
            booking.guest.name,
            booking.guest.email_addr,
        ]


class TalkVotingReport(ReportView):
    title = 'Talk voting'
    headings = ['ID', 'Title', 'Proposer', 'Number of votes', 'Number interested']

    def get_queryset(self):
        return Proposal.objects.accepted_talks().annotate(
            num_votes=Count('vote'),
            num_interested=Sum(Case(When(vote__is_interested=True, then=Value(1)), default=Value(0)), output_field=IntegerField())
        ).order_by('-num_interested', '-num_votes')

    def presenter(self, proposal):
        link = {
            'href': reverse('reports:cfp_proposal', args=[proposal.proposal_id]),
            'text': proposal.proposal_id,
        }

        return [
            link,
            proposal.title,
            proposal.proposer.name,
            proposal.num_votes,
            proposal.num_interested,
        ]


class TalkVotingByUserReport(ReportView):
    title = 'Talk voting by user'
    headings = ['Name', 'Number of votes', 'Number interested']

    def get_queryset(self):
        return User.objects.annotate(
            num_votes=Count('vote'),
            num_interested=Sum(Case(When(vote__is_interested=True, then=Value(1)), default=Value(0)), output_field=IntegerField())
        ).order_by('-num_votes', '-num_interested')

    def presenter(self, user):
        return [
            user.name,
            user.num_votes,
            user.num_interested,
        ]


class VolunteerSetupReport(ReportView, PeopleMixin):
    title = 'Volunteers to setup'
    
    def get_queryset(self):
        return User.objects.filter(volunteer_setup=True)


class VolunteerSessionChairReport(ReportView, PeopleMixin):
    title = 'Volunteers to chair sessions'
    
    def get_queryset(self):
        return User.objects.filter(volunteer_session_chair=True)


class VolunteerVideorReport(ReportView, PeopleMixin):
    title = 'Volunteers to help with videoing'
    
    def get_queryset(self):
        return User.objects.filter(volunteer_videoer=True)


class VolunteerRegDeskReport(ReportView, PeopleMixin):
    title = 'Volunteers to staff registration desk'
    
    def get_queryset(self):
        return User.objects.filter(volunteer_reg_desk=True)


class DinnerMixin:
    headings = ['Name', 'Email address', 'Complimentary', 'Starter', 'Main', 'Pudding']

    def presenter(self, booking):
        return [
            booking.guest.name,
            booking.guest.email_addr,
            '✘' if booking.paid_booking else '✔',
            booking.starter,
            booking.main,
            booking.pudding,
        ]


class ConferenceDinnerReport(DinnerMixin, ReportView):
    title = 'Conference dinner'

    def get_queryset(self):
        DinnerBooking.objects.filter(venue='conference').select_related('guest').order_by('guest__name')


class ContributorsDinnerReport(DinnerMixin, ReportView):
    title = "Contributors' dinner"

    def get_queryset(self):
        DinnerBooking.objects.filter(venue='contributors').select_related('guest').order_by('guest__name')


reports = [
    AttendanceByDayReport,
    TicketSummaryReport,
    ChildrensDaySummaryReport,
    TicketSalesReport,
    OrdersReport,
    UnpaidOrdersReport,
    TicketsReport,
    UnclaimedTicketsReport,
    FreeTicketsReport,
    DjangoGirlsTicketsReport,
    ChildrensDayTicketsReport,
    TalkVotingReport,
    TalkVotingByUserReport,
    CFPPropsals,
    CFPPropsalsForEducationTrack,
    CFPPropsalsPlanToAccept,
    CFPPropsalsPlanToAcceptOfTypeOther,
    CFPPropsalsPlanToAcceptWithGrantApplications,
    CFPPropsalsPlanToReject,
    CFPPropsalsNoDecision,
    CFPPropsalsAimedAtNewProgrammers,
    CFPPropsalsAimedAtTeachers,
    CFPPropsalsAimedAtDataScientists,
    SpeakersSeekingMentorReport,
    AttendeesWithAccessibilityReqs,
    AttendeesWithChildcareReqs,
    AttendeesWithDietaryReqs,
    GrantApplications,
    GrantApplicationsWithFundsOffered,
    PeopleReport,
    ContributorReport,
    AccommodationReport,
    AccommodationBookingsReport,
    UKPAReport,
    CandidateReport,
    VolunteerSetupReport,
    VolunteerSessionChairReport,
    VolunteerVideorReport,
    VolunteerRegDeskReport,
    TicketHoldersWithIncompleteNameReport,
    ConferenceDinnerReport,
    ContributorsDinnerReport,
]
