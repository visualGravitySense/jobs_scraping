from django.contrib import admin
from django.contrib.admin import register
from .models import City, Language, Vacancy, Error, Url


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
