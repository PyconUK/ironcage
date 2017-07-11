from django.conf.urls import url

from . import views

app_name = 'trustee_nominations'

urlpatterns = [
    url(r'^nominations/new/$', views.new_nomination, name='new_nomination'),
    url(r'^nominations/(?P<nomination_id>\w+)/$', views.nomination, name='nomination'),
    url(r'^nominations/(?P<nomination_id>\w+)/edit/$', views.nomination_edit, name='nomination_edit'),
]
