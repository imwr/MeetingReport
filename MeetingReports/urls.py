from django.conf.urls import url
from MeetingReports import views

urlpatterns = [
    url(r'^meeting-reports/$', views.IndexView.as_view()),
    url(r'^meeting-reports/(?P<meeting_id>\d+)$', views.MeetingDetailView.as_view(), name='detail'),
    url(r'^meeting-reports/list', views.MeetingListView.as_view(), name='list'),
    url(r'^meeting-reports/get_last_userreport', views.get_last_userreport),
    url(r'^meeting-reports/send_email', views.SendEmail.as_view()),
]
