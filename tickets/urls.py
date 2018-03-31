from django.conf.urls import url

from . import views
from payments import views as payment_views

app_name = 'tickets'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/(?P<order_id>\w+)/edit/$', payment_views.order_edit, name='order_edit'),
    url(r'^tickets/(?P<ticket_id>\w+)/$', views.ticket, name='ticket'),
    url(r'^tickets/(?P<ticket_id>\w+)/edit/$', views.ticket_edit, name='ticket_edit'),
    url(r'^invitations/(?P<token>\w+)/$', views.ticket_invitation, name='ticket_invitation'),
]
