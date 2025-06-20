import time
import re
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class CVKeskusScraper:
    """Скрапер для CV Keskus (Эстония)"""
    
    name = "cvkeskus"
    base_url = "https://www.cvkeskus.ee"
    search_url = "https://www.cvkeskus.ee/toopakkumised"
    
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'et-EE,et;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def setup_driver(self):
        """Настройка Chrome WebDriver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--lang=en")  # Force English language
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Try to use existing ChromeDriver first
            try:
                self.driver = uc.Chrome(
                    options=options,
                    version_main=None,  # Let it auto-detect Chrome version
                    driver_executable_path=None,  # Let it find existing driver
                    browser_executable_path=None  # Let it find existing browser
                )
            except Exception as e:
                logger.warning(f"Failed to use existing ChromeDriver: {e}")
                # Try with different version
                try:
                    self.driver = uc.Chrome(
                        options=options,
                        version_main=None,  # Let it auto-detect
                        driver_executable_path=None,
                        browser_executable_path=None
                    )
                except Exception as e2:
                    logger.error(f"Failed to setup ChromeDriver with auto-detect: {e2}")
                    raise
            
            logger.info("Chrome WebDriver setup successful")
            
            # Set default page load timeout
            self.driver.set_page_load_timeout(30)
            
        except Exception as e:
            logger.error(f"Error setting up Chrome WebDriver: {e}")
            raise
        
    def handle_cookie_consent(self):
        """Handle cookie consent popup"""
        try:
            # Wait for cookie consent button
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
            )
            accept_button.click()
            logger.info("Accepted cookie consent")
            time.sleep(2)  # Wait for popup to disappear
        except TimeoutException:
            logger.info("No cookie consent popup found")
        except Exception as e:
            logger.warning(f"Error handling cookie consent: {e}")
    
    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing Chrome WebDriver: {e}")
            
    def extract_salary(self, salary_text):
        """Извлечение зарплаты из текста"""
        if not salary_text:
            return None, None
            
        # Паттерны для зарплаты
        patterns = [
            r'(\d+)\s*-\s*(\d+)\s*€',  # 3000 - 4000 €
            r'From\s*(\d+)\s*€',     # From 2500 €
            r'Up to\s*(\d+)\s*€',    # Up to 3500 €
            r'(\d+)\s*€',            # 3400 €
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary_text)
            if match:
                if len(match.groups()) == 2:
                    return int(match.group(1)), int(match.group(2))
                else:
                    amount = int(match.group(1))
                    if 'From' in salary_text:
                        return amount, None
                    elif 'Up to' in salary_text:
                        return None, amount
                    else:
                        return amount, amount
        return None, None
    
    def parse_job_card(self, job_element):
        """Парсинг одной вакансии"""
        try:
            # Get all the job data from data-props attribute
            try:
                data_props = job_element.get_attribute("data-props")
                if data_props:
                    job_data = json.loads(data_props)
                else:
                    job_data = {}
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Could not parse data-props: {e}")
                job_data = {}
            
            # Title
            title = ""
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2, h3, .job-title")
                title = title_element.text.strip()
            except NoSuchElementException:
                title = job_data.get("title", "")
            
            if not title:
                logger.error("Empty job title found")
                return None
            
            # Company name
            company = ""
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, ".company-name, .employer")
                company = company_element.text.strip()
            except NoSuchElementException:
                company = job_data.get("company_name", "")
            
            # Location
            location = job_data.get("location", "")
            if not location:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, ".location, .job-location")
                    location = location_element.text.strip()
                except NoSuchElementException:
                    pass
            
            # Job URL
            url = ""
            try:
                link_element = job_element.find_element(By.CSS_SELECTOR, "a")
                url = link_element.get_attribute("href")
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
            except NoSuchElementException:
                url = job_data.get("url", "")
            
            # Employment type
            employment_type = job_data.get("employment_type", "")
            if not employment_type:
                try:
                    type_elements = job_element.find_elements(By.CSS_SELECTOR, ".job-type, .employment-type")
                    employment_type = type_elements[0].text.strip() if type_elements else ""
                except (NoSuchElementException, IndexError):
                    pass
            
            return {
            'title': title,
            'company': company,
            'location': location,
                'url': url,
                'employment_type': employment_type,
                'raw_data': job_data  # Store raw data for debugging
            }
            
        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None
    
    def search_jobs(self, keywords="", location="", max_pages=1, limit=None):
        """Поиск вакансий на CV Keskus"""
        try:
            # Формируем URL для поиска - используем фильтры для IT вакансий
            search_params = {
                'op': 'search',
                'search[job_salary]': '3',  # Все зарплаты
                'ga_track': 'results',  # Изменено с 'all_ads' на 'results'
                'search[categories][]': ['8', '23'],  # IT и маркетинг категории
                'badge[categories][]': ['8', '23'],  # Добавляем badge фильтры
                'search[keyword]': keywords,
                'search[expires_days]': '',
                'search[job_lang]': '',
                'search[salary]': ''
            }

            if location:
                search_params['search[location]'] = location

            # Строим URL
            url = f"{self.search_url}?{urllib.parse.urlencode(search_params, doseq=True)}"
            logger.info(f"Searching jobs at: {url}")

            # Получаем страницу
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Сохраняем для отладки
            with open("cvkeskus_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)

            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            jobs = []

            # Ищем вакансии - используем правильный селектор на основе реальной структуры
            job_elements = soup.find_all('article', attrs={'data-component': 'jobad'})

            if not job_elements:
                # Альтернативный поиск по атрибуту data-href
                job_elements = soup.find_all(attrs={'data-href': lambda x: x and 'toopakkumised' in x})
                logger.info(f"Found {len(job_elements)} jobs with data-href selector")
            else:
                logger.info(f"Found {len(job_elements)} jobs with data-component='jobad' selector")

            if not job_elements:
                # Последняя попытка - найти все ссылки на вакансии
                job_links = soup.find_all('a', href=lambda x: x and '/toopakkumised/' in x)
                logger.info(f"Found {len(job_links)} job links")

                for link in job_links:
                    job_data = self._parse_job_from_link(link, soup)
                    if job_data:
                        jobs.append(job_data)
            else:
                # Парсим найденные элементы вакансий
                for job_element in job_elements:
                    job_data = self._parse_job_element(job_element)
                    if job_data:
                        jobs.append(job_data)

            # Ограничиваем количество результатов если указан limit
            if limit and len(jobs) > limit:
                jobs = jobs[:limit]
                logger.info(f"Limited results to {limit} jobs")

            logger.info(f"Successfully parsed {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []

    def _parse_job_element(self, job_element):
        """Парсинг элемента вакансии"""
        try:
            job_data = {}
            
            # Заголовок вакансии - ищем в h2 элементе
            title_elem = job_element.find('h2')
            if title_elem:
                job_data['title'] = title_elem.get_text(strip=True)
            
            # Если заголовок не найден в h2, ищем в div с классом text-slate-500
            if not job_data.get('title'):
                title_elem = job_element.find('div', class_='text-slate-500 visited-group:text-neutral-700 lg:hidden font-extrabold')
                if title_elem:
                    job_data['title'] = title_elem.get_text(strip=True)
            
            # Компания - ищем в элементе с классом job-company
            company_elem = job_element.find(class_='job-company')
            if company_elem:
                job_data['company'] = company_elem.get_text(strip=True)
            
            # Локация - ищем в элементе с классом location
            location_elem = job_element.find(class_='location')
            if location_elem:
                job_data['location'] = location_elem.get_text(strip=True)
            
            # Если локация не найдена, ищем в div с классом text-sm lg:hidden
            if not job_data.get('location'):
                location_div = job_element.find('div', class_='text-sm lg:hidden')
                if location_div:
                    job_data['location'] = location_div.get_text(strip=True)
            
            # Дата публикации - ищем в span с текстом, содержащим "tagasi"
            date_spans = job_element.find_all('span')
            for span in date_spans:
                text = span.get_text(strip=True)
                if 'tagasi' in text:
                    job_data['posted_date'] = text
                    break
            
            # Ссылка на вакансию - ищем в элементе с атрибутом data-href
            href_elem = job_element.find(attrs={'data-href': True})
            if href_elem:
                href = href_elem.get('data-href')
                if href:
                    job_data['url'] = self.base_url + href
            
            # Если ссылка не найдена в data-href, ищем в a элементе
            if not job_data.get('url'):
                link_elem = job_element.find('a', href=True)
                if link_elem:
                    href = link_elem.get('href')
                    if href and href.startswith('/'):
                        job_data['url'] = self.base_url + href
                    elif href:
                        job_data['url'] = href
            
            # Дополнительная информация из data-props
            data_props = job_element.get('data-props')
            if data_props:
                try:
                    props = json.loads(data_props)
                    job_data['raw_data'] = props
                    if 'job_id' in props:
                        job_data['job_id'] = props['job_id']
                except:
                    pass
            
            # Добавляем источник
            job_data['source'] = 'cvkeskus'
            job_data['scraped_at'] = datetime.now().isoformat()
            
            return job_data if job_data.get('title') else None
            
        except Exception as e:
            logger.error(f"Error parsing job element: {e}")
            return None
    
    def _parse_job_from_link(self, link, soup):
        """Парсинг вакансии из ссылки"""
        try:
            job_data = {}
            
            # Получаем заголовок из текста ссылки
            job_data['title'] = link.get_text(strip=True)
            job_data['url'] = self.base_url + link.get('href', '')
            
            # Ищем родительский элемент для получения дополнительной информации
            parent = link.find_parent()
            if parent:
                # Компания
                company_elem = parent.find(class_=lambda x: x and 'company' in x.lower())
                if company_elem:
                    job_data['company'] = company_elem.get_text(strip=True)
                
                # Локация
                location_elem = parent.find(class_=lambda x: x and 'location' in x.lower())
                if location_elem:
                    job_data['location'] = location_elem.get_text(strip=True)
            
            job_data['source'] = 'cvkeskus'
            job_data['scraped_at'] = datetime.now().isoformat()
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing job from link: {e}")
            return None

def cvkeskus_scraper(search_url=None, limit=None):
    """Функция для использования в других модулях"""
    scraper = CVKeskusScraper()
    return scraper.search_jobs(limit=limit)