from django.contrib import admin
from .models import Technology, Project, ProjectImage, PortfolioVersion

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color']
    search_fields = ['name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_featured', 'is_public', 'created_at']
    list_filter = ['is_featured', 'is_public', 'created_at']
    search_fields = ['title', 'user__username']
    filter_horizontal = ['technologies']

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['project', 'caption', 'is_primary', 'order']
    list_filter = ['is_primary']
    search_fields = ['project__title', 'caption']

@admin.register(PortfolioVersion)
class PortfolioVersionAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'is_active', 'public_url', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['projects']
