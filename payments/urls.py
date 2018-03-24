from django.conf.urls import url

from . import views
from payments import views as payment_views

app_name = 'payments'

urlpatterns = [
    url(r'^orders/(?P<invoice_id>\w+)/$', payment_views.order, name='order'),
    url(r'^invoice/(?P<invoice_id>\w+)/$', views.invoice, name='invoice'),
]
