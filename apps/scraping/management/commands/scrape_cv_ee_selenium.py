import logging
from django.core.management.base import BaseCommand
from apps.scraping.scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper
from apps.scraping.models import Job, JobScore

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape jobs from cv.ee using Selenium'

    def add_arguments(self, parser):
        parser.add_argument('--keywords', nargs='+', type=str, help='Keywords to search for')
        parser.add_argument('--location', type=str, help='Location to search in')
        parser.add_argument('--max-pages', type=int, default=3, help='Maximum number of pages to scrape')

    def handle(self, *args, **options):
        keywords = options.get('keywords', [])
        location = options.get('location')
        max_pages = options.get('max_pages', 3)

        self.stdout.write(self.style.SUCCESS(f'Starting cv.ee scraper with keywords: {keywords}, location: {location}'))
        
        try:
            # Инициализация парсера
            scraper = CVeeSeleniumScraper(headless=True)
            
            # Поиск вакансий
            jobs = scraper.search_jobs(keywords=keywords, location=location, max_pages=max_pages)
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(jobs)} jobs'))
            
            # Сохранение вакансий в базу
            for job_data in jobs:
                try:
                    # Получение детальной информации
                    details = scraper.get_job_details(job_data['url'])
                    job_data.update(details)
                    
                    # Создание или обновление вакансии
                    job, created = Job.objects.update_or_create(
                        url=job_data['url'],
                        defaults={
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'location': job_data['location'],
                            'description': job_data.get('description', ''),
                            'source': job_data['source'],
                            'posted_date': job_data.get('posted_date'),
                            'employment_type': job_data.get('employment_type'),
                            'salary': job_data.get('salary')
                        }
                    )
                    
                    # Создание оценки для вакансии
                    JobScore.objects.get_or_create(job=job)
                    
                    status = 'Created' if created else 'Updated'
                    self.stdout.write(self.style.SUCCESS(f'{status} job: {job.title}'))
                    
                except Exception as e:
                    logger.error(f"Error processing job {job_data.get('url')}: {str(e)}")
                    continue
            
            self.stdout.write(self.style.SUCCESS('Finished scraping cv.ee'))
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 