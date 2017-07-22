from django.conf.urls import url

from . import reports, views

app_name = 'reports'

urlpatterns = [
    url(report.path(), report.as_view(), name=report.url_name())
    for report in reports.reports
]

urlpatterns.append(url('^$', views.index, name='index'))
