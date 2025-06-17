from django.urls import path
from . import views
from .views import scraper_progress_api

app_name = 'scraping'

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('scrapers/', views.ScraperManagementView.as_view(), name='scraper_management'),
    path('export/csv/', views.export_jobs_csv, name='export_csv'),
    path('export/excel/', views.export_jobs_excel, name='export_excel'),
    path('scraping/api/scrapers/progress/<str:scraper_name>/', scraper_progress_api, name='scraper_progress_api'),
    path('scraping/api/scrapers/test/<int:scraper_id>/', views.test_scraper_api, name='test_scraper_api'),
] 