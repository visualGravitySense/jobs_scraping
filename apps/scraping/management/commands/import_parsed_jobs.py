import json
from django.core.management.base import BaseCommand
from apps.scraping.models import ParsedJob, ParsedCompany

class Command(BaseCommand):
    help = 'Import parsed job data from cv_ee_jobs.json into ParsedJob and ParsedCompany models'

    def handle(self, *args, **options):
        try:
            with open('cv_ee_jobs.json', 'r', encoding='utf-8') as f:
                jobs = json.load(f)

            for job_data in jobs:
                # Create or update ParsedCompany
                company, _ = ParsedCompany.objects.update_or_create(
                    employer_id=job_data['employerId'],
                    defaults={
                        'name': job_data['company'],
                        'job_count': ParsedCompany.objects.filter(employer_id=job_data['employerId']).count() + 1
                    }
                )

                # Create or update ParsedJob
                ParsedJob.objects.update_or_create(
                    id=job_data['id'],
                    defaults={
                        'title': job_data['title'],
                        'company': job_data['company'],
                        'location': job_data['location'],
                        'salary_from': job_data['salaryFrom'],
                        'salary_to': job_data['salaryTo'],
                        'remote_work': job_data['remoteWork'],
                        'publish_date': job_data['publishDate'],
                        'expiration_date': job_data['expirationDate'],
                        'description': job_data['description'] if job_data['description'] != 'null' else None,
                        'employer': company
                    }
                )

            self.stdout.write(self.style.SUCCESS('Successfully imported parsed job data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {e}')) 