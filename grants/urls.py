from django.conf.urls import url

from . import views

app_name = 'grants'

urlpatterns = [
    url(r'^applications/new/$', views.new_application, name='new_application'),
    url(r'^applications/(?P<application_id>\w+)/$', views.application, name='application'),
    url(r'^applications/(?P<application_id>\w+)/edit/$', views.application_edit, name='application_edit'),
    url(r'^applications/(?P<application_id>\w+)/delete/$', views.application_delete, name='application_delete'),
]
