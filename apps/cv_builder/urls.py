from django.urls import path
from . import views

app_name = 'cv_builder'

urlpatterns = [
    path('', views.cv_dashboard, name='dashboard'),
    path('create/', views.cv_version_create, name='cv_version_create'),
    path('<int:pk>/', views.cv_version_detail, name='cv_version_detail'),
    path('<int:pk>/edit/', views.cv_version_edit, name='cv_version_edit'),
    path('<int:pk>/export/', views.cv_export_pdf, name='cv_export_pdf'),
    path('experience/create/', views.experience_create, name='experience_create'),
    path('education/create/', views.education_create, name='education_create'),
] 