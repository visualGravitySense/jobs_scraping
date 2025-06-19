#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы CVKeskus скрапера
"""

import sys
import os
import json
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cvkeskus_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.scraping.scrapers.cvkeskus_scraper import CVKeskusScraper

def test_cvkeskus_scraper():
    """Тестирование CVKeskus скрапера"""
    print("\n" + "="*80)
    print("🔍 Testing CVKeskus scraper...")
    print("="*80 + "\n")
    try:
        scraper = CVKeskusScraper()
        jobs = scraper.search_jobs(keywords="", location="", max_pages=1)
        print(f"Найдено вакансий: {len(jobs)}")
        if jobs:
            print("\nПоследняя вакансия:")
            last_job = jobs[-1]
            print(json.dumps(last_job, ensure_ascii=False, indent=2))
        else:
            print("Вакансии не найдены!")
        # Сохраняем результат
        with open(f"cvkeskus_jobs_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_cvkeskus_scraper() 