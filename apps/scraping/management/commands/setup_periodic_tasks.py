from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Set up periodic tasks for automated job scraping'

    def handle(self, *args, **options):
        self.stdout.write('Setting up periodic tasks...')
        
        # Create schedules
        daily_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        
        weekly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=7,
            period=IntervalSchedule.DAYS,
        )
        
        # Daily CV Keskus scraping
        daily_scraping, created = PeriodicTask.objects.get_or_create(
            name='Daily CV Keskus Scraping',
            defaults={
                'task': 'apps.scraping.tasks.scrape_cv_keskus',
                'interval': daily_schedule,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created daily CV Keskus scraping task'))
        else:
            self.stdout.write('Daily CV Keskus scraping task already exists')
        
        # Weekly comprehensive scraping
        weekly_scraping, created = PeriodicTask.objects.get_or_create(
            name='Weekly Comprehensive Scraping',
            defaults={
                'task': 'apps.scraping.tasks.scrape_all_sources',
                'interval': weekly_schedule,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created weekly comprehensive scraping task'))
        else:
            self.stdout.write('Weekly comprehensive scraping task already exists')
        
        # Daily cleanup
        daily_cleanup, created = PeriodicTask.objects.get_or_create(
            name='Daily Job Cleanup',
            defaults={
                'task': 'apps.scraping.tasks.cleanup_old_jobs',
                'interval': daily_schedule,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created daily cleanup task'))
        else:
            self.stdout.write('Daily cleanup task already exists')
        
        # Daily analytics generation
        daily_analytics, created = PeriodicTask.objects.get_or_create(
            name='Daily Analytics Generation',
            defaults={
                'task': 'apps.scraping.tasks.generate_job_analytics',
                'interval': daily_schedule,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created daily analytics generation task'))
        else:
            self.stdout.write('Daily analytics generation task already exists')
        
        self.stdout.write(self.style.SUCCESS('Periodic tasks setup completed!')) 