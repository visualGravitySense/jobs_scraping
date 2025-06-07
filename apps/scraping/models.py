import jsonfield
from django.db import models
from django.utils import timezone

from .utils import from_cyrillic_to_eng


def default_urls():
    return {"work": "", "rabota": "", "dou": "", "djinni": ""}

class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,
                            verbose_name='Название города',
                            unique=True)
    slug = models.CharField(max_length=50, blank=True, unique=True)
    
    class Meta:
        verbose_name = 'Название города'
        verbose_name_plural = 'Название городов'
        
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = from_cyrillic_to_eng(str(self.name))
        super().save(*args, **kwargs)


class Language(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,
                            verbose_name='Язык программирования',
                            unique=True)
    slug = models.CharField(max_length=50, blank=True, unique=True)

    class Meta:
        verbose_name = 'Язык программирования'
        verbose_name_plural = 'Языки программирования'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = from_cyrillic_to_eng(str(self.name))
        super().save(*args, **kwargs)


class Vacancy(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.URLField(unique=True)
    title = models.CharField(max_length=250,
                            verbose_name='Заголовок вакансии')
    company = models.CharField(max_length=250,
                            verbose_name='Компания')
    description = models.TextField(verbose_name='Описание вакансии')
    city = models.ForeignKey('City', on_delete = models.CASCADE, verbose_name='Город')
    language = models.ForeignKey('Language', on_delete=models.CASCADE, verbose_name='Язык программирования')
    timestamp = models.DateField(auto_now_add=True)
    salary_min = models.IntegerField(default=None, null=True, blank=True, verbose_name='Минимальная зарплата')
    salary_max = models.IntegerField(default=None, null=True, blank=True, verbose_name='Максимальная зарплата')
    salary_currency = models.CharField(max_length=10, default='EUR', verbose_name='Валюта зарплаты')

    class Meta:
        verbose_name = 'Название вакансии'
        verbose_name_plural = 'Названия вакансий'

    def __str__(self):
        return self.title

class Error(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateField(auto_now_add=True)
    data = jsonfield.JSONField()


class Url(models.Model):
    id = models.AutoField(primary_key=True)
    city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name='Город')
    language = models.ForeignKey('Language', on_delete=models.CASCADE, verbose_name='Язык программирования')
    url_data = jsonfield.JSONField(default=default_urls)

    class Meta:
        unique_together = ("city", "language")

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    url = models.URLField(unique=True)
    source = models.CharField(max_length=50)
    posted_date = models.DateTimeField(null=True, blank=True)
    employment_type = models.CharField(max_length=100, null=True, blank=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-posted_date', '-created_at']

    def __str__(self):
        return f"{self.title} at {self.company}"

class JobScore(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='score', null=True, blank=True)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Score'
        verbose_name_plural = 'Job Scores'
        ordering = ['-score', '-updated_at']

    def __str__(self):
        return f"Score for {self.job.title}: {self.score}"

class LinkedInAuth(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'LinkedIn Auth'
        verbose_name_plural = 'LinkedIn Auths'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

class ParsedCompany(models.Model):
    employer_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    job_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parsed Company'
        verbose_name_plural = 'Parsed Companies'

    def __str__(self):
        return self.name

class ParsedJob(models.Model):
    id = models.BigIntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    salary_from = models.FloatField(null=True, blank=True)
    salary_to = models.FloatField(null=True, blank=True)
    remote_work = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    employer = models.ForeignKey(ParsedCompany, on_delete=models.CASCADE, related_name='jobs')

    class Meta:
        verbose_name = 'Parsed Job'
        verbose_name_plural = 'Parsed Jobs'

    def __str__(self):
        return f"{self.title} at {self.company}"