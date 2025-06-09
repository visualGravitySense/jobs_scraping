from django.core.management.base import BaseCommand
from apps.scraping.models import Scraper

class Command(BaseCommand):
    help = 'Create scraper records in database'

    def handle(self, *args, **options):
        self.stdout.write("=== Создание записей скраперов ===")
        
        # Создаем скрапер для CV.ee
        scraper1, created1 = Scraper.objects.get_or_create(
            name='CV.ee Scraper',
            defaults={
                'source': 'cv_ee',
                'status': 'idle',
                'config': {'url': 'https://cv.ee/search'}
            }
        )
        
        if created1:
            self.stdout.write("✓ Создан скрапер CV.ee")
        else:
            self.stdout.write("• Скрапер CV.ee уже существует")
        
        # Создаем скрапер для CVKeskus
        scraper2, created2 = Scraper.objects.get_or_create(
            name='CVKeskus Scraper',
            defaults={
                'source': 'cvkeskus',
                'status': 'idle',
                'config': {'url': 'https://cvkeskus.ee'}
            }
        )
        
        if created2:
            self.stdout.write("✓ Создан скрапер CVKeskus")
        else:
            self.stdout.write("• Скрапер CVKeskus уже существует")
        
        # Показываем все скраперы
        all_scrapers = Scraper.objects.all()
        self.stdout.write(f"\n=== Всего скраперов в БД: {all_scrapers.count()} ===")
        for scraper in all_scrapers:
            self.stdout.write(f"- {scraper.name} ({scraper.source}) - {scraper.status}")
        
        self.stdout.write("\n✅ Готово! Теперь скраперы будут доступны в веб-интерфейсе.") 