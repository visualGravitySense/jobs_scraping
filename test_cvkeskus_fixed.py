#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленного CV Keskus скрапера
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.scraping.scrapers.cvkeskus_scraper import CVKeskusScraper

def test_cvkeskus_scraper():
    """Тестирование CV Keskus скрапера"""
    print("=" * 80)
    print("🔍 Testing FIXED CVKeskus scraper...")
    print("=" * 80)
    
    try:
        # Создаем экземпляр скрапера
        scraper = CVKeskusScraper()
        
        # Ищем вакансии без фильтров
        jobs = scraper.search_jobs()
        
        print(f"Найдено вакансий: {len(jobs)}")
        
        if jobs:
            print("\nПоследняя вакансия:")
            print(json.dumps(jobs[-1], indent=2, ensure_ascii=False))
            
            # Показываем первые 5 вакансий
            print(f"\nПервые 5 вакансий:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"{i}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
        
        return len(jobs)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании скрапера: {e}")
        return 0

if __name__ == "__main__":
    job_count = test_cvkeskus_scraper()
    print(f"\n✅ Тест завершен. Найдено вакансий: {job_count}") 