from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

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


# Новая модель Company согласно плану MVP
class Company(models.Model):
    COMPANY_SIZES = [
        ('startup', 'Startup'),
        ('small', 'Small (1-50)'),
        ('medium', 'Medium (51-200)'),
        ('large', 'Large (200+)'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    size = models.CharField(max_length=50, choices=COMPANY_SIZES, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


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
    data = models.JSONField()


class Url(models.Model):
    id = models.AutoField(primary_key=True)
    city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name='Город')
    language = models.ForeignKey('Language', on_delete=models.CASCADE, verbose_name='Язык программирования')
    url_data = models.JSONField(default=default_urls)

    class Meta:
        unique_together = ("city", "language")

# Обновленная модель Job согласно плану MVP
class Job(models.Model):
    EXPERIENCE_LEVELS = [
        ('junior', 'Junior'),
        ('middle', 'Middle'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('any', 'Any'),
    ]
    
    SOURCE_SITES = [
        ('cvonline', 'CV Online'),
        ('cv_ee', 'CV.ee'),
        ('linkedin', 'LinkedIn'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    company_name = models.CharField(max_length=255, default='')  # Для backward compatibility
    location = models.CharField(max_length=100, default='')
    description = models.TextField(default='')
    requirements = models.TextField(blank=True, default='')
    source_url = models.URLField(unique=True)
    source_site = models.CharField(max_length=50, choices=SOURCE_SITES, default='other')
    
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='EUR')
    
    is_remote = models.BooleanField(default=False)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_LEVELS, default='any')
    employment_type = models.CharField(max_length=100, null=True, blank=True)
    
    posted_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-posted_date', '-created_at']

    def __str__(self):
        return f"{self.title} at {self.company_name}"

# Обновленная модель JobScore согласно плану MVP
class JobScore(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='jobscore')
    relevance_score = models.IntegerField(default=0)  # 0-100
    skill_match_score = models.IntegerField(default=0)  # 0-100  
    salary_score = models.IntegerField(default=0)  # 0-100
    location_score = models.IntegerField(default=0)  # 0-100
    calculated_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Score'
        verbose_name_plural = 'Job Scores'
        ordering = ['-relevance_score', '-updated_at']

    def __str__(self):
        return f"Score for {self.job.title}: {self.relevance_score}"

# Новая модель UserProfile согласно плану MVP
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(help_text="Навыки через запятую")
    min_salary = models.IntegerField(null=True, blank=True)
    location_preference = models.CharField(max_length=100, blank=True)
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    is_notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.username}"

# Новая модель Application для трекинга откликов согласно плану MVP  
class Application(models.Model):
    STATUS_CHOICES = [
        ('interested', 'Интересно'),
        ('applied', 'Отклик отправлен'),
        ('interview', 'Интервью'),
        ('rejected', 'Отказ'),
        ('accepted', 'Принят'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='interested')
    applied_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        unique_together = ['user', 'job']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.job.title} ({self.status})"

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

class Scraper(models.Model):
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=50, choices=Job.SOURCE_SITES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scraper'
        verbose_name_plural = 'Scrapers'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.source})"

    def test_scraper(self):
        """Test the scraper and return first job"""
        from .scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper
        from .scrapers.cvkeskus_scraper import cvkeskus_scraper
        from .scrapers.linkedin_scraper import LinkedInScraper

        try:
            if self.source == 'cv_ee':
                scraper = CVeeSeleniumScraper()
                jobs = scraper.search_jobs(keywords=['python'], location='Tallinn', max_pages=1)
                return jobs[0] if jobs else None
            elif self.source == 'cvkeskus':
                # Используем конкретный URL для CVKeskus
                search_url = "https://www.cvkeskus.ee/toopakkumised?op=search&search%5Bjob_salary%5D=3&ga_track=all_ads&search%5Bcategories%5D%5B%5D=8&search%5Bcategories%5D%5B%5D=23&search%5Bkeyword%5D=&search%5Bexpires_days%5D=&search%5Bjob_lang%5D=&search%5Bsalary%5D="
                jobs = cvkeskus_scraper(search_url)
                return jobs[0] if jobs else None
            elif self.source == 'linkedin':
                scraper = LinkedInScraper()
                jobs = scraper.search_jobs(['python'], 'Estonia', 1)
                return jobs[0] if jobs else None
            return None
        except Exception as e:
            return {'error': str(e)}

    def get_latest_jobs(self, limit=10):
        """Get the latest jobs from the scraper source"""
        from .scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper
        from .scrapers.cvkeskus_scraper import cvkeskus_scraper
        from .scrapers.linkedin_scraper import LinkedInScraper

        try:
            if self.source == 'cv_ee':
                scraper = CVeeSeleniumScraper()
                jobs = scraper.search_jobs(keywords=['python', 'django', 'javascript'], location='Tallinn', max_pages=2)
                return jobs[:limit] if jobs else []
            elif self.source == 'cvkeskus':
                # Используем конкретный URL для CVKeskus
                search_url = "https://www.cvkeskus.ee/toopakkumised?op=search&search%5Bjob_salary%5D=3&ga_track=all_ads&search%5Bcategories%5D%5B%5D=8&search%5Bcategories%5D%5B%5D=23&search%5Bkeyword%5D=&search%5Bexpires_days%5D=&search%5Bjob_lang%5D=&search%5Bsalary%5D="
                jobs = cvkeskus_scraper(search_url)
                return jobs[:limit] if jobs else []
            elif self.source == 'linkedin':
                scraper = LinkedInScraper()
                jobs = scraper.search_jobs(['python', 'developer', 'software'], 'Estonia', 2)
                return jobs[:limit] if jobs else []
            return []
        except Exception as e:
            return {'error': str(e)}