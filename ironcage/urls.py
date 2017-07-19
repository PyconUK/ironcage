from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin

import accounts.views
import ironcage.views


urlpatterns = [
    url(r'^accounts/register/', accounts.views.register, name='register'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^cfp/', include('cfp.urls')),
    url(r'^grants/', include('grants.urls')),
    url(r'^profile/', include('accounts.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^tickets/', include('tickets.urls')),
    url(r'^ukpa/', include('ukpa.urls')),
    url(r'^$', ironcage.views.index, name='index'),
    url(r'^500/$', ironcage.views.error, name='error'),
    url(r'^log/$', ironcage.views.log, name='log'),
    url(r'^avatar/', include('avatar.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
