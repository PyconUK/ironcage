from django.conf.urls import url

from . import views

app_name = 'tickets'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/(?P<order_id>\d+)/$', views.order, name='order'),
]
