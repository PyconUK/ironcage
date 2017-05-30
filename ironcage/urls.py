from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^profile/', include('accounts.urls')),
    url(r'^tickets/', include('tickets.urls')),
]
