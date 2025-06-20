from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.name

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Отклик отправлен'),
        ('reviewing', 'Рассматривается'),
        ('interview', 'Собеседование'),
        ('technical', 'Техническое собеседование'),
        ('offer', 'Предложение'),
        ('rejected', 'Отказ'),
        ('accepted', 'Принят'),
        ('withdrawn', 'Отозван'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    position = models.CharField(max_length=200)
    job_url = models.URLField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    
    # Версии CV и портфолио
    cv_version = models.ForeignKey('cv_builder.CVVersion', on_delete=models.SET_NULL, null=True, blank=True)
    portfolio_version = models.ForeignKey('portfolio.PortfolioVersion', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Статус и даты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Дополнительная информация
    notes = models.TextField(blank=True)
    recruiter_name = models.CharField(max_length=100, blank=True)
    recruiter_email = models.EmailField(blank=True)
    
    def __str__(self):
        return f"{self.position} at {self.company.name}"

class Interview(models.Model):
    INTERVIEW_TYPES = [
        ('phone', 'Телефонное'),
        ('video', 'Видео'),
        ('onsite', 'Личная встреча'),
        ('technical', 'Техническое'),
        ('hr', 'HR'),
    ]
    
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(help_text='Длительность в минутах')
    interviewer_name = models.CharField(max_length=100, blank=True)
    interviewer_position = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.application.position} - {self.get_interview_type_display()}"
