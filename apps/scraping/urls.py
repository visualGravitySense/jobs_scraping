from django.urls import path
from .views import (
    home_view, list_view, 
    LinkedInAuthView, LinkedInCallbackView, parsed_jobs_list_view,
    analytics_dashboard_view, export_jobs_csv, export_jobs_excel, export_analytics_report
)

urlpatterns = [
    path('', home_view, name='home'),
    path('list/', list_view, name='list'),
    # LinkedIn authentication URLs
    path('linkedin/auth/', LinkedInAuthView.as_view(), name='linkedin_auth'),
    path('linkedin/callback/', LinkedInCallbackView.as_view(), name='linkedin_callback'),
    path('jobs/', list_view, name='jobs_list'),
    path('parsed-jobs/', parsed_jobs_list_view, name='parsed_jobs_list'),
    path('analytics/', analytics_dashboard_view, name='analytics_dashboard'),
    path('export/csv/', export_jobs_csv, name='export_jobs_csv'),
    path('export/excel/', export_jobs_excel, name='export_jobs_excel'),
    path('export/analytics/', export_analytics_report, name='export_analytics_report'),
] 