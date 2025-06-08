from django.core.management.base import BaseCommand
from apps.scraping.models import ParsedJob, ParsedCompany
from apps.scraping.scrapers.cvkeskus_selenium import cvkeskus_selenium_scraper

CVKESKUS_URL = "https://www.cvkeskus.ee/toopakkumised?op=search&search%5Bjob_salary%5D=3&ga_track=homepage&search%5Blocations%5D%5B%5D=3&search%5Bcategories%5D%5B%5D=8&search%5Bkeyword%5D="

class Command(BaseCommand):
    help = 'Scrape CV Keskus and import jobs into ParsedJob and ParsedCompany.'

    def handle(self, *args, **options):
        jobs = cvkeskus_selenium_scraper(CVKESKUS_URL)
        count = 0
        for job_data in jobs:
            if not job_data['company']:
                continue
            company, _ = ParsedCompany.objects.get_or_create(
                employer_id=job_data['employerId'],
                defaults={'name': job_data['company']}
            )
            ParsedJob.objects.update_or_create(
                id=hash(job_data['title'] + (job_data['company'] or '')),  # Use a hash as a fallback unique ID
                defaults={
                    'title': job_data['title'],
                    'company': job_data['company'],
                    'location': job_data['location'],
                    'salary_from': job_data['salaryFrom'],
                    'salary_to': job_data['salaryTo'],
                    'remote_work': job_data['remoteWork'],
                    'publish_date': job_data['publishDate'],
                    'expiration_date': job_data['expirationDate'],
                    'description': job_data['description'],
                    'employer': company
                }
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {count} jobs from CV Keskus.")) 