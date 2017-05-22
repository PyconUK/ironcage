from django.conf.urls import url

from . import views

app_name = 'tickets'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/(?P<order_id>\w+)/$', views.order, name='order'),
    url(r'^orders/(?P<order_id>\w+)/payment/$', views.order_payment, name='order_payment'),
    url(r'^tickets/(?P<ticket_id>\w+)/$', views.ticket, name='ticket'),
    url(r'^invitations/(?P<token>\w+)/$', views.ticket_invitation, name='ticket_invitation'),
]
