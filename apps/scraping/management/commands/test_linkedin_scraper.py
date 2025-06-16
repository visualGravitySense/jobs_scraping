from django.core.management.base import BaseCommand
from apps.scraping.scrapers.linkedin_scraper import LinkedInScraper
from apps.scraping.models import Job
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test LinkedIn scraper functionality'

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование LinkedIn скрапера ===")
        
        try:
            # Создаем экземпляр скрапера
            scraper = LinkedInScraper()
            self.stdout.write("✓ LinkedIn скрапер создан")
            
            # Тестируем поиск вакансий
            self.stdout.write("🔍 Поиск вакансий...")
            jobs = scraper.search_jobs(['python', 'django'], 'Estonia', 2)
            
            self.stdout.write(f"✓ Найдено {len(jobs)} вакансий")
            
            # Показываем первые несколько вакансий
            for i, job in enumerate(jobs[:5]):
                self.stdout.write(f"\n--- Вакансия {i+1} ---")
                self.stdout.write(f"Название: {job.get('title', 'N/A')}")
                self.stdout.write(f"Компания: {job.get('company', 'N/A')}")
                self.stdout.write(f"Локация: {job.get('location', 'N/A')}")
                self.stdout.write(f"URL: {job.get('url', 'N/A')}")
                if job.get('salary_min'):
                    self.stdout.write(f"Зарплата: {job.get('salary_min')} - {job.get('salary_max', 'N/A')}")
            
            # Тестируем сохранение в базу данных
            self.stdout.write("\n💾 Сохранение в базу данных...")
            jobs_created = 0
            
            for job_data in jobs:
                try:
                    job, created = Job.objects.get_or_create(
                        source_url=job_data.get('url', ''),
                        defaults={
                            'title': job_data.get('title', ''),
                            'company_name': job_data.get('company', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description', ''),
                            'source_site': 'linkedin',
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'is_active': True
                        }
                    )
                    if created:
                        jobs_created += 1
                        self.stdout.write(f"✓ Создана: {job.title} в {job.company_name}")
                    else:
                        self.stdout.write(f"• Уже существует: {job.title}")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка сохранения: {str(e)}")
            
            self.stdout.write(f"\n✅ Тест завершен! Создано {jobs_created} новых вакансий из {len(jobs)} найденных")
            
        except Exception as e:
            self.stdout.write(f"❌ Ошибка тестирования: {str(e)}")
            logger.error(f"LinkedIn scraper test error: {str(e)}") 