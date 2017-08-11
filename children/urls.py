from django.conf.urls import url

from . import views

app_name = 'children'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/(?P<order_id>\w+)/$', views.order, name='order'),
    url(r'^orders/(?P<order_id>\w+)/edit/$', views.order_edit, name='order_edit'),
    url(r'^orders/(?P<order_id>\w+)/payment/$', views.order_payment, name='order_payment'),
]
