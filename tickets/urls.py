from django.conf.urls import url

from . import views

app_name = 'tickets'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/confirm/$', views.order_confirm, name='order_confirm'),
    url(r'^orders/edit/$', views.order_edit, name='order_edit'),
    url(r'^tickets/(?P<ticket_id>\w+)/$', views.ticket, name='ticket'),
    url(r'^tickets/(?P<ticket_id>\w+)/edit/$', views.ticket_edit, name='ticket_edit'),
    url(r'^invitations/(?P<token>\w+)/$', views.ticket_invitation, name='ticket_invitation'),
]
