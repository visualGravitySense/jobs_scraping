from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.scraping.tasks import scrape_all_sources, calculate_job_scores, send_job_notifications
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run all job scrapers and related tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run tasks asynchronously using Celery',
        )
        parser.add_argument(
            '--no-notifications',
            action='store_true',
            help='Skip sending notifications',
        )
        parser.add_argument(
            '--no-scoring',
            action='store_true',
            help='Skip job scoring calculation',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting job scraping at {timezone.now()}')
        )

        try:
            if options['async']:
                # Запускаем задачи асинхронно через Celery
                self.stdout.write('Running scrapers asynchronously...')
                
                # Запускаем парсинг
                scrape_task = scrape_all_sources.delay()
                self.stdout.write(f'Scraping task started: {scrape_task.id}')
                
                # Запускаем расчет скоров
                if not options['no_scoring']:
                    scoring_task = calculate_job_scores.delay()
                    self.stdout.write(f'Scoring task started: {scoring_task.id}')
                
                # Запускаем отправку уведомлений
                if not options['no_notifications']:
                    notification_task = send_job_notifications.delay()
                    self.stdout.write(f'Notification task started: {notification_task.id}')
                
            else:
                # Запускаем задачи синхронно
                self.stdout.write('Running scrapers synchronously...')
                
                # Парсинг
                scrape_result = scrape_all_sources()
                self.stdout.write(f'Scraping result: {scrape_result}')
                
                # Расчет скоров
                if not options['no_scoring']:
                    scoring_result = calculate_job_scores()
                    self.stdout.write(f'Scoring result: {scoring_result}')
                
                # Отправка уведомлений
                if not options['no_notifications']:
                    notification_result = send_job_notifications()
                    self.stdout.write(f'Notification result: {notification_result}')

            self.stdout.write(
                self.style.SUCCESS(f'Job scraping completed at {timezone.now()}')
            )

        except Exception as e:
            logger.error(f"Error in run_all_scrapers command: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            ) 