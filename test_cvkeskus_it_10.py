#!/usr/bin/env python3
"""
Тестовый скрипт для проверки последних 10 IT вакансий CV Keskus
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.scraping.scrapers.cvkeskus_scraper import CVKeskusScraper

def test_cvkeskus_it_10():
    """Тестирование CV Keskus скрапера для последних 10 IT вакансий"""
    print("=" * 80)
    print("🔍 Testing CVKeskus IT scraper - Last 10 jobs...")
    print("=" * 80)
    
    try:
        # Создаем экземпляр скрапера
        scraper = CVKeskusScraper()
        
        # Ищем последние 10 IT вакансий
        jobs = scraper.search_jobs(limit=10)
        
        print(f"Найдено IT вакансий: {len(jobs)}")
        
        if jobs:
            print(f"\nПоследние {len(jobs)} IT вакансий:")
            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job.get('title', 'N/A')}")
                print(f"   Компания: {job.get('company', 'N/A')}")
                print(f"   Локация: {job.get('location', 'N/A')}")
                print(f"   Дата: {job.get('posted_date', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')}")
                print()
            
            # Сохраняем в JSON файл
            with open("cvkeskus_it_10_jobs.json", "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"✅ Результаты сохранены в cvkeskus_it_10_jobs.json")
        
        return len(jobs)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании скрапера: {e}")
        return 0

if __name__ == "__main__":
    job_count = test_cvkeskus_it_10()
    print(f"\n✅ Тест завершен. Найдено IT вакансий: {job_count}") 