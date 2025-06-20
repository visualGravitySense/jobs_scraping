from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.portfolio_dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('versions/', views.portfolio_version_list, name='version_list'),
    path('versions/create/', views.portfolio_version_create, name='version_create'),
    path('versions/<int:pk>/', views.portfolio_version_detail, name='version_detail'),
] 