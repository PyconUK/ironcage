from django.conf.urls import url

from . import views

app_name = 'cfp'

urlpatterns = [
    url(r'^proposals/new/$', views.new_proposal, name='new_proposal'),
    url(r'^proposals/(?P<proposal_id>\w+)/$', views.proposal, name='proposal'),
    url(r'^proposals/(?P<proposal_id>\w+)/edit/$', views.proposal_edit, name='proposal_edit'),
    url(r'^proposals/(?P<proposal_id>\w+)/delete/$', views.proposal_delete, name='proposal_delete'),
    url(r'^voting/$', views.voting_index, name='voting_index'),
    url(r'^voting/reviewed/$', views.voting_reviewed_proposals, name='voting_reviewed_proposals'),
    url(r'^voting/unreviewed/$', views.voting_unreviewed_proposals, name='voting_unreviewed_proposals'),
    url(r'^voting/of-interest/$', views.voting_proposals_of_interest, name='voting_proposals_of_interest'),
    url(r'^voting/not-of-interest/$', views.voting_proposals_not_of_interest, name='voting_proposals_not_of_interest'),
    url(r'^voting/proposals/(?P<proposal_id>\w+)/$', views.voting_proposal, name='voting_proposal'),
]
