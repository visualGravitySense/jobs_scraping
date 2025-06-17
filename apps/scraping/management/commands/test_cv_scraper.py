from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class Command(BaseCommand):
    help = 'Test CV.ee scraper functionality'

    def handle(self, *args, **options):
        self.stdout.write("=== Тестирование CV.ee скрапера ===")
        
        # Настройка Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.stdout.write("✓ Chrome WebDriver успешно запущен")
            
            # Загружаем страницу
            url = 'https://cv.ee/search'
            self.stdout.write(f"Загружаем страницу: {url}")
            driver.get(url)
            time.sleep(8)  # Увеличиваем время ожидания
            
            # Сохраняем HTML для проверки
            with open('cv_ee_debug.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            self.stdout.write("✓ HTML сохранен в cv_ee_debug.html")
            
            # Парсим HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Проверяем различные селекторы
            self.stdout.write("\n=== Проверка селекторов ===")
            
            # Попробуем найти вакансии
            job_cards_1 = soup.find_all('li', class_=lambda x: x and 'vacancies-list__item' in x)
            self.stdout.write(f"Найдено вакансий (selector 1): {len(job_cards_1)}")
            
            job_cards_2 = soup.find_all('div', class_=lambda x: x and 'vacancy-item' in x)
            self.stdout.write(f"Найдено вакансий (div vacancy-item): {len(job_cards_2)}")
            
            job_cards_3 = soup.find_all('li')
            self.stdout.write(f"Всего <li> элементов: {len(job_cards_3)}")
            
            # Попробуем другие селекторы
            job_cards_4 = soup.find_all('article')
            self.stdout.write(f"Найдено <article> элементов: {len(job_cards_4)}")
            
            job_cards_5 = soup.find_all('div', class_=lambda x: x and 'vacancy' in x)
            self.stdout.write(f"Найдено div с 'vacancy': {len(job_cards_5)}")
            
            # Новые селекторы
            job_cards_6 = soup.find_all('div', class_=lambda x: x and 'job-item' in x)
            self.stdout.write(f"Найдено div с 'job-item': {len(job_cards_6)}")
            
            job_cards_7 = soup.find_all('div', attrs={'data-testid': 'job-card'})
            self.stdout.write(f"Найдено div с data-testid='job-card': {len(job_cards_7)}")
            
            # Ищем ссылки на вакансии
            job_links = soup.find_all('a', href=lambda x: x and '/vacancy/' in x)
            self.stdout.write(f"Найдено ссылок на вакансии (/vacancy/): {len(job_links)}")
            
            # Если есть ссылки на вакансии, покажем первые несколько
            if job_links:
                self.stdout.write("\n=== Первые найденные ссылки на вакансии ===")
                for i, link in enumerate(job_links[:5]):
                    self.stdout.write(f"Ссылка {i+1}: {link.get('href')} - '{link.text.strip()[:50]}...'")
            
            # Если есть вакансии, попробуем распарсить первую
            if job_cards_1:
                self.stdout.write("\n=== Парсинг первой вакансии (selector 1) ===")
                card = job_cards_1[0]
                
                # Title
                title_tag = card.find('a', class_=lambda x: x and 'vacancy-item__title' in x)
                self.stdout.write(f"Название: {title_tag.text.strip() if title_tag else 'НЕ НАЙДЕНО'}")
                
                # Company
                company_link = card.find('a', href=lambda x: x and 'employer' in x)
                self.stdout.write(f"Компания: {company_link.text.strip() if company_link else 'НЕ НАЙДЕНО'}")
                
                # Location
                location_div = card.find('div', class_=lambda x: x and 'vacancy-item__locations' in x)
                if location_div:
                    location_text = location_div.get_text(strip=True)
                    location = location_text.replace('...', '').strip()
                    self.stdout.write(f"Локация: {location}")
                else:
                    self.stdout.write("Локация: НЕ НАЙДЕНО")
            
            elif job_links:
                self.stdout.write("\n=== Пробуем через найденные ссылки ===")
                first_link = job_links[0]
                parent = first_link.find_parent()
                if parent:
                    self.stdout.write(f"HTML родительского элемента: {str(parent)[:300]}...")
            
            # Проверим заголовок страницы
            title = soup.find('title')
            self.stdout.write(f"\nЗаголовок страницы: {title.text if title else 'НЕ НАЙДЕН'}")
            
            driver.quit()
            self.stdout.write("\n✓ Тест завершен")
            
        except Exception as e:
            self.stdout.write(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc() 