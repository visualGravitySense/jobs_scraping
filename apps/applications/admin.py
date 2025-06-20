from django.contrib import admin
from .models import Company, JobApplication, Interview

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'industry', 'size']
    list_filter = ['industry', 'size']
    search_fields = ['name', 'website']

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'position', 'status', 'applied_date', 'last_updated']
    list_filter = ['status', 'applied_date', 'last_updated']
    search_fields = ['position', 'company__name', 'user__username']
    readonly_fields = ['applied_date', 'last_updated']

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'scheduled_date', 'is_completed']
    list_filter = ['interview_type', 'is_completed', 'scheduled_date']
    search_fields = ['application__position', 'interviewer_name']
