from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.applications_dashboard, name='dashboard'),
    path('applications/', views.job_application_list, name='application_list'),
    path('applications/create/', views.job_application_create, name='application_create'),
    path('applications/<int:pk>/', views.job_application_detail, name='application_detail'),
    path('applications/<int:pk>/edit/', views.job_application_edit, name='application_edit'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('interviews/', views.interview_list, name='interview_list'),
    path('interviews/create/', views.interview_create, name='interview_create'),
] 