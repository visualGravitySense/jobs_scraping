from django.core.management.base import BaseCommand
from apps.scraping.models import Vacancy
from apps.scraping.services import JobScoringService

class Command(BaseCommand):
    help = 'Score all existing vacancies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keywords',
            nargs='+',
            type=str,
            help='Keywords to use for relevance scoring',
            default=['python', 'django', 'flask', 'fastapi', 'postgresql', 'mysql']
        )

    def handle(self, *args, **options):
        keywords = options['keywords']
        vacancies = Vacancy.objects.all()
        
        self.stdout.write(f"Starting to score {vacancies.count()} vacancies...")
        
        for vacancy in vacancies:
            try:
                score = JobScoringService.score_vacancy(vacancy, keywords)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Scored vacancy '{vacancy.title}': "
                        f"total={score.total_score:.2f}, "
                        f"relevance={score.relevance_score:.2f}, "
                        f"salary={score.salary_score:.2f}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error scoring vacancy '{vacancy.title}': {str(e)}"
                    )
                )
                
        self.stdout.write(self.style.SUCCESS("Finished scoring vacancies")) 