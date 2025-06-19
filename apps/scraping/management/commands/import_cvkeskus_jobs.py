from django.core.management.base import BaseCommand
from apps.scraping.tasks import scrape_cvkeskus_jobs
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import jobs from CVKeskus'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run task asynchronously using Celery',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting CVKeskus job import at {timezone.now()}')
        )

        try:
            if options['async']:
                # Run asynchronously with Celery
                task = scrape_cvkeskus_jobs.delay()
                self.stdout.write(f'Task started with ID: {task.id}')
            else:
                # Run synchronously
                result = scrape_cvkeskus_jobs()
                self.stdout.write(f'Import completed: {result}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during import: {str(e)}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'CVKeskus job import finished at {timezone.now()}')
        ) 