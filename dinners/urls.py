from django.conf.urls import url

from . import views

app_name = 'dinners'

urlpatterns = [
    url(r'^contributors-dinner/$', views.contributors_dinner, name='contributors_dinner'),
    url(r'^conference-dinner/$', views.conference_dinner, name='conference_dinner'),
    url(r'^conference-dinner/payment/$', views.conference_dinner_payment, name='conference_dinner_payment'),
    url(r'^conference-dinner/receipt/$', views.conference_dinner_receipt, name='conference_dinner_receipt'),
]
