from django.conf.urls import url

from . import views

app_name = 'accommodation'

urlpatterns = [
    url(r'^bookings/new/$', views.new_booking, name='new_booking'),
    url(r'^bookings/payment/$', views.booking_payment, name='booking_payment'),
    url(r'^bookings/receipt/$', views.booking_receipt, name='booking_receipt'),
]
