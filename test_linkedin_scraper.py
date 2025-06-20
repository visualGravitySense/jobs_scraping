#!/usr/bin/env python3
"""
Тестовый скрипт для проверки LinkedIn скрапера
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.scraping.scrapers.linkedin_scraper import LinkedInScraper

def test_linkedin_scraper():
    """Тестирование LinkedIn скрапера"""
    print("=" * 80)
    print("🔍 Testing LinkedIn scraper...")
    print("=" * 80)
    
    try:
        # Создаем экземпляр скрапера
        scraper = LinkedInScraper()
        
        # Ищем вакансии с теми же параметрами, что и в задаче
        jobs = scraper.search_jobs(
            keywords=["software engineer", "developer", "programmer"],
            location="Estonia",
            max_pages=1  # Начнем с одной страницы
        )
        
        print(f"Найдено вакансий: {len(jobs)}")
        
        if jobs:
            print(f"\nПервые {min(10, len(jobs))} вакансий:")
            for i, job in enumerate(jobs[:10], 1):
                print(f"{i}. {job.get('title', 'N/A')}")
                print(f"   Компания: {job.get('company', 'N/A')}")
                print(f"   Локация: {job.get('location', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')}")
                print()
            
            # Проверяем на дубликаты по URL
            urls = [job.get('url') for job in jobs if job.get('url')]
            unique_urls = set(urls)
            duplicate_urls = len(urls) - len(unique_urls)
            
            print(f"Всего URL: {len(urls)}")
            print(f"Уникальных URL: {len(unique_urls)}")
            print(f"Дубликатов URL: {duplicate_urls}")
            
            # Проверяем на дубликаты по заголовку и компании
            job_signatures = []
            for job in jobs:
                signature = f"{job.get('title', '')} - {job.get('company', '')}"
                job_signatures.append(signature)
            
            unique_signatures = set(job_signatures)
            duplicate_signatures = len(job_signatures) - len(unique_signatures)
            
            print(f"Дубликатов по заголовку+компания: {duplicate_signatures}")
            
            # Показываем дубликаты
            if duplicate_signatures > 0:
                print(f"\nДубликаты:")
                seen = set()
                for i, signature in enumerate(job_signatures):
                    if signature in seen:
                        print(f"  Дубликат {i+1}: {signature}")
                    else:
                        seen.add(signature)
            
            # Сохраняем в JSON файл
            with open("linkedin_jobs_debug.json", "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"✅ Результаты сохранены в linkedin_jobs_debug.json")
        
        return len(jobs)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании скрапера: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    job_count = test_linkedin_scraper()
    print(f"\n✅ Тест завершен. Найдено вакансий: {job_count}") 