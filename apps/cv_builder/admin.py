from django.contrib import admin
from .models import CVTemplate, Skill, Experience, Education, CVVersion

@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'category']
    list_filter = ['level', 'category']
    search_fields = ['name']

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'position', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'start_date']
    search_fields = ['company', 'position', 'user__username']

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'degree', 'field_of_study', 'start_date']
    list_filter = ['start_date']
    search_fields = ['institution', 'degree', 'user__username']

@admin.register(CVVersion)
class CVVersionAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'version_number', 'template', 'is_active', 'created_at']
    list_filter = ['is_active', 'template', 'created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['experiences', 'education', 'skills'] 