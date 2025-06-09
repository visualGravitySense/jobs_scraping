#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def test_cv_ee_scraper():
    print("=== Тестирование CV.ee скрапера ===")
    
    # Настройка Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        print("✓ Chrome WebDriver успешно запущен")
        
        # Загружаем страницу
        url = 'https://www.cv.ee/et/vacancies'
        print(f"Загружаем страницу: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Сохраняем HTML для проверки
        with open('cv_ee_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ HTML сохранен в cv_ee_debug.html")
        
        # Парсим HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Проверяем различные селекторы
        print("\n=== Проверка селекторов ===")
        
        # Попробуем найти вакансии
        job_cards_1 = soup.find_all('li', class_=lambda x: x and 'vacancies-list__item' in x)
        print(f"Найдено вакансий (selector 1): {len(job_cards_1)}")
        
        job_cards_2 = soup.find_all('li', class_='jsx-1871295890')
        print(f"Найдено вакансий (selector 2): {len(job_cards_2)}")
        
        job_cards_3 = soup.find_all('li')
        print(f"Всего <li> элементов: {len(job_cards_3)}")
        
        # Если есть вакансии, попробуем распарсить первую
        if job_cards_1:
            print("\n=== Парсинг первой вакансии ===")
            card = job_cards_1[0]
            
            # Title
            title_tag = card.find('a', class_=lambda x: x and 'vacancy-item__title' in x)
            print(f"Название: {title_tag.text.strip() if title_tag else 'НЕ НАЙДЕНО'}")
            
            # Company
            company_link = card.find('a', href=lambda x: x and 'employer' in x)
            print(f"Компания: {company_link.text.strip() if company_link else 'НЕ НАЙДЕНО'}")
            
            # Location
            location_div = card.find('div', class_=lambda x: x and 'vacancy-item__locations' in x)
            if location_div:
                location_text = location_div.get_text(strip=True)
                location = location_text.replace('...', '').strip()
                print(f"Локация: {location}")
            else:
                print("Локация: НЕ НАЙДЕНО")
        
        driver.quit()
        print("\n✓ Тест завершен")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cv_ee_scraper() 