from django.contrib import admin
from django.contrib.admin import register
from .models import (
    City, Language, Vacancy, Error, Url, ParsedJob, ParsedCompany,
    Company, Job, JobScore, UserProfile, Application
)


@register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    

@register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")


@register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        "id", "url", "title", "company",
        "description", "city", "language", "timestamp"
                    )


@register(Error)
class ErrorAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "data")


@register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "language")


@admin.register(ParsedCompany)
class ParsedCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'employer_id', 'job_count', 'last_updated')
    search_fields = ('name', 'employer_id')


@admin.register(ParsedJob)
class ParsedJobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'salary_from', 'salary_to', 'remote_work', 'publish_date', 'expiration_date')
    list_filter = ('remote_work', 'publish_date', 'expiration_date')
    search_fields = ('title', 'company', 'description')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'location', 'website', 'created_at')
    list_filter = ('size', 'created_at')
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'location', 'source_site', 'salary_min', 'salary_max', 'is_remote', 'posted_date', 'is_active')
    list_filter = ('source_site', 'is_remote', 'experience_level', 'is_active', 'posted_date')
    search_fields = ('title', 'company_name', 'location', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)


class JobScoreInline(admin.StackedInline):
    model = JobScore
    extra = 0
    readonly_fields = ('calculated_at', 'updated_at')


@admin.register(JobScore)
class JobScoreAdmin(admin.ModelAdmin):
    list_display = ('job', 'relevance_score', 'skill_match_score', 'salary_score', 'location_score', 'calculated_at')
    list_filter = ('calculated_at',)
    readonly_fields = ('calculated_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'min_salary', 'location_preference', 'is_notifications_enabled', 'created_at')
    list_filter = ('is_notifications_enabled', 'created_at')
    search_fields = ('user__username', 'user__email', 'skills')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'applied_at', 'reminder_date', 'updated_at')
    list_filter = ('status', 'applied_at', 'reminder_date')
    search_fields = ('user__username', 'job__title', 'job__company_name')
    readonly_fields = ('created_at', 'updated_at')
