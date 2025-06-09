import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('jobs_scraping')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    # Парсинг вакансий каждые 4 часа
    'scrape-all-sources': {
        'task': 'apps.scraping.tasks.scrape_all_sources',
        'schedule': crontab(minute=0, hour='*/4'),  # Каждые 4 часа
    },
    
    # Расчет скоров каждые 2 часа
    'calculate-job-scores': {
        'task': 'apps.scraping.tasks.calculate_job_scores',
        'schedule': crontab(minute=30, hour='*/2'),  # Каждые 2 часа в 30 минут
    },
    
    # Отправка уведомлений каждый час
    'send-job-notifications': {
        'task': 'apps.scraping.tasks.send_job_notifications',
        'schedule': crontab(minute=15),  # Каждый час в 15 минут
    },
    
    # Напоминания о заявках каждый день в 9:00
    'application-reminders': {
        'task': 'apps.scraping.tasks.update_application_reminders',
        'schedule': crontab(hour=9, minute=0),  # Каждый день в 9:00
    },
    
    # Очистка старых данных каждый день в 2:00
    'cleanup-old-jobs': {
        'task': 'apps.scraping.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 2:00
    },
    
    # Генерация аналитики каждые 6 часов
    'generate-analytics': {
        'task': 'apps.scraping.tasks.generate_job_analytics',
        'schedule': crontab(minute=0, hour='*/6'),  # Каждые 6 часов
    },
}

# Настройка временной зоны для периодических задач
app.conf.timezone = 'Europe/Tallinn'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 