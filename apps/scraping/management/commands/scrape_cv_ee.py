from django.core.management.base import BaseCommand
from django.db import transaction
from apps.scraping.models import Vacancy, City, Language
from apps.scraping.scrapers.cv_ee_scraper import CVeeScraper
from apps.scraping.services import JobScoringService

class Command(BaseCommand):
    help = 'Scrape jobs from cv.ee'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keywords',
            nargs='+',
            type=str,
            help='Keywords to search for',
            default=['python', 'django', 'flask']
        )
        parser.add_argument(
            '--location',
            type=str,
            help='Location to search in',
            default='Estonia'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            help='Maximum number of pages to scrape',
            default=5
        )

    def handle(self, *args, **options):
        keywords = options['keywords']
        location = options['location']
        max_pages = options['max_pages']

        self.stdout.write(f"Starting cv.ee scraper for keywords: {keywords}")
        
        scraper = CVeeScraper()
        jobs = scraper.search_jobs(keywords, location, max_pages)
        
        self.stdout.write(f"Found {len(jobs)} jobs")
        
        # Get or create default city and language
        city, _ = City.objects.get_or_create(name=location)
        language, _ = Language.objects.get_or_create(name='Python')
        
        for job_data in jobs:
            try:
                with transaction.atomic():
                    # Get detailed job information
                    details = scraper.get_job_details(job_data['url'])
                    if not details:
                        continue
                    
                    # Create or update vacancy
                    vacancy, created = Vacancy.objects.update_or_create(
                        url=job_data['url'],
                        defaults={
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'description': details['description'],
                            'city': city,
                            'language': language,
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'salary_currency': 'EUR'
                        }
                    )
                    
                    # Score the vacancy
                    JobScoringService.score_vacancy(vacancy, keywords)
                    
                    status = "Created" if created else "Updated"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{status} vacancy: {vacancy.title} at {vacancy.company}"
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing job {job_data.get('title')}: {str(e)}"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS("Finished scraping cv.ee")) 