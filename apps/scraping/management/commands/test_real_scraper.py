from django.core.management.base import BaseCommand
from apps.scraping.scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper
from apps.scraping.models import Job

class Command(BaseCommand):
    help = 'Test real CVeeSeleniumScraper'

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование реального скрапера CVeeSeleniumScraper ===")
        
        # Подсчитываем существующие вакансии
        existing_jobs = Job.objects.filter(source_site='cv_ee').count()
        self.stdout.write(f"Существующих вакансий в БД: {existing_jobs}")
        
        # Запускаем скрапер
        scraper = CVeeSeleniumScraper()
        
        try:
            jobs_created = scraper.scrape_jobs()
            self.stdout.write(f"✓ Скрапер завершил работу. Создано вакансий: {jobs_created}")
            
            # Подсчитываем новое количество вакансий
            new_jobs_count = Job.objects.filter(source_site='cv_ee').count()
            self.stdout.write(f"Общее количество вакансий в БД: {new_jobs_count}")
            
            # Показываем несколько последних вакансий
            if new_jobs_count > existing_jobs:
                latest_jobs = Job.objects.filter(source_site='cv_ee').order_by('-created_at')[:5]
                self.stdout.write("\n=== Последние созданные вакансии ===")
                for job in latest_jobs:
                    self.stdout.write(f"- {job.title} | {job.company_name} | {job.location} | {job.source_url}")
            
        except Exception as e:
            self.stdout.write(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc() 