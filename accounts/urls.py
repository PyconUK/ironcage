from django.conf.urls import url

from . import views

app_name = 'accounts'

urlpatterns = [
    url(r'^$', views.profile, name='profile'),
    url(r'^edit/$', views.edit_profile, name='edit_profile'),
]
