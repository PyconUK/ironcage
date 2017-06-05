from django.conf.urls import url, include
from django.contrib import admin

import accounts.views


urlpatterns = [
    url(r'^accounts/register/', accounts.views.register, name='register'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^profile/', include('accounts.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^tickets/', include('tickets.urls')),
]
