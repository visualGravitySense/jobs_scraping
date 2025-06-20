"""digo_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.scraping.views import home_view, list_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.scraping.urls')),
    path('accounts/', include(('apps.accounts.urls', 'accounts'))),
    
    # Новые приложения CV сервиса
    path('cv/', include('apps.cv_builder.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('applications/', include('apps.applications.urls')),
    path('templates/', include('apps.templates_mgr.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
