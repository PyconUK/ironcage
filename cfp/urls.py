from django.conf.urls import url

from . import views

app_name = 'cfp'

urlpatterns = [
    url(r'^proposals/new/$', views.new_proposal, name='new_proposal'),
    url(r'^proposals/(?P<proposal_id>\w+)/$', views.proposal, name='proposal'),
    url(r'^proposals/(?P<proposal_id>\w+)/edit/$', views.proposal_edit, name='proposal_edit'),
    url(r'^proposals/(?P<proposal_id>\w+)/delete/$', views.proposal_delete, name='proposal_delete'),
]
