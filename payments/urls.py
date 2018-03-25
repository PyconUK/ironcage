from django.conf.urls import url

from . import views

app_name = 'payments'

urlpatterns = [
    url(r'^orders/(?P<invoice_id>\w+)/$', views.order, name='order'),
    url(r'^payment/(?P<payment_id>\w+)/$', views.payment, name='payment'),
    url(r'^orders/(?P<order_id>\w+)/payment/$', views.invoice_payment, name='invoice_payment'),
]
