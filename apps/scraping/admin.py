from django.contrib import admin
from django.contrib.admin import register
from .models import City, Language, Vacancy, Error, Url, ParsedJob, ParsedCompany


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
