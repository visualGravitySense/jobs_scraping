from django.urls import path
from . import views

app_name = 'scraping'

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('scrapers/', views.ScraperManagementView.as_view(), name='scraper_management'),
    path('export/csv/', views.export_jobs_csv, name='export_csv'),
    path('export/excel/', views.export_jobs_excel, name='export_excel'),
] 