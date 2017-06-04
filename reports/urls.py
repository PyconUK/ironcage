from django.conf.urls import url

from . import views

app_name = 'reports'

urlpatterns = [
    url(report.path(), report.as_view(), name=report.url_name())
    for report in views.reports
]

urlpatterns.append(url('^$', views.index, name='index'))
