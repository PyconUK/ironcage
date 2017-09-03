from django.conf.urls import url

from . import reports, views

app_name = 'reports'

urlpatterns = [
    url(report.path(), report.as_view(), name=report.url_name())
    for report in reports.reports
]

urlpatterns.extend([
    url(r'^accounts/users/(?P<user_id>\w+)/$', views.accounts_user, name='accounts_user'),
    url(r'^cfp/proposals/(?P<proposal_id>\w+)/$', views.cfp_proposal, name='cfp_proposal'),
    url(r'^grants/applications/(?P<application_id>\w+)/$', views.grants_application, name='grants_application'),
    url(r'^tickets/orders/(?P<order_id>\w+)/$', views.tickets_order, name='tickets_order'),
    url(r'^tickets/tickets/(?P<ticket_id>\w+)/$', views.tickets_ticket, name='tickets_ticket'),
    url('^$', views.index, name='index'),
])
