import time
import json
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

class CVeeSeleniumScraper:
    BASE_URL = "https://www.cv.ee/et/search"

    def __init__(self, headless: bool = True):
        """
        Инициализация Selenium-парсера для cv.ee.
        :param headless: Запускать браузер в фоновом режиме (без GUI).
        """
        chrome_options = uc.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Использование undetected-chromedriver для обхода защиты
        self.driver = uc.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)

    def _wait_and_find_element(self, by: By, value: str, timeout: int = 10):
        """Ожидание и поиск элемента с обработкой ошибок."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.error(f"Элемент не найден: {value}")
            return None

    def _wait_and_find_elements(self, by: By, value: str, timeout: int = 10):
        """Ожидание и поиск элементов с обработкой ошибок."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except TimeoutException:
            logger.error(f"Элементы не найдены: {value}")
            return []

    def _handle_cookie_consent(self):
        """Обработка баннера согласия на cookies."""
        try:
            # Ищем кнопку согласия на cookies
            consent_selectors = [
                "button[data-testid='accept-all-cookies']",
                "button:contains('Nõustun kõigiga')",
                ".cookie-consent button",
                "[id*='cookie'] button",
                "[class*='cookie'] button"
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = self._wait_and_find_element(By.CSS_SELECTOR, selector, timeout=3)
                    if consent_button and consent_button.is_displayed():
                        consent_button.click()
                        logger.info("Согласие на cookies принято")
                        time.sleep(1)
                        return True
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Не удалось обработать баннер cookies: {str(e)}")
        return False

    def _extract_json_data(self):
        """Извлечение данных из JSON на странице."""
        try:
            # Ищем script с данными Next.js
            script_element = self._wait_and_find_element(By.ID, "__NEXT_DATA__")
            if script_element:
                json_text = script_element.get_attribute("textContent")
                data = json.loads(json_text)
                
                # Извлекаем данные о вакансиях
                search_results = data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                vacancies = search_results.get("vacancies", [])
                
                logger.info(f"Найдено {len(vacancies)} вакансий в JSON данных")
                return vacancies
        except Exception as e:
            logger.error(f"Ошибка при извлечении JSON данных: {str(e)}")
        return []

    def search_jobs(self, keywords: List[str] = None, location: str = "Tallinn", max_pages: int = 5) -> List[Dict]:
        """
        Поиск вакансий на cv.ee с помощью Selenium.
        :param keywords: Список ключевых слов для поиска.
        :param location: Локация для поиска.
        :param max_pages: Максимальное количество страниц для парсинга.
        :return: Список словарей с данными о вакансиях.
        """
        all_jobs = []
        try:
            # Формируем URL с параметрами поиска
            search_params = {
                "limit": "20",
                "offset": "0",
                "categories[0]": "INFORMATION_TECHNOLOGY",
                "towns[0]": "312",  # Tallinn
                "fuzzy": "true"
            }
            
            if keywords:
                search_params["q"] = " ".join(keywords)
            
            # Строим URL
            params_str = "&".join([f"{k}={v}" for k, v in search_params.items()])
            search_url = f"{self.BASE_URL}?{params_str}"
            
            self.driver.get(search_url)
            logger.info(f"Открыта страница: {search_url}")
            
            # Обработка согласия на cookies
            self._handle_cookie_consent()
            
            # Ожидание загрузки страницы
            time.sleep(3)
            
            # Парсинг страниц
            for page in range(max_pages):
                logger.info(f"Парсинг страницы {page + 1}")
                
                # Сначала пытаемся извлечь данные из JSON
                json_vacancies = self._extract_json_data()
                if json_vacancies:
                    for vacancy in json_vacancies:
                        job_data = self._parse_vacancy_from_json(vacancy)
                        if job_data:
                            all_jobs.append(job_data)
                else:
                    # Если JSON не найден, парсим HTML
                    html_jobs = self._parse_html_jobs()
                    all_jobs.extend(html_jobs)
                
                # Проверка наличия следующей страницы
                if page < max_pages - 1:
                    if not self._go_to_next_page():
                        logger.info("Достигнут конец списка вакансий")
                        break
                    time.sleep(2)

        except Exception as e:
            logger.error(f"Ошибка при поиске вакансий: {str(e)}")
        finally:
            self.driver.quit()
            logger.info("Браузер закрыт")

        return all_jobs

    def _parse_vacancy_from_json(self, vacancy: Dict) -> Optional[Dict]:
        """Парсинг вакансии из JSON данных."""
        try:
            job_data = {
                "title": vacancy.get("positionTitle", ""),
                "company": vacancy.get("employerName", ""),
                "location": "Tallinn",  # По умолчанию, так как фильтруем по Таллинну
                "url": f"https://www.cv.ee/et/vacancy/{vacancy.get('id', '')}",
                "description": vacancy.get("positionContent", "") or "",
                "source": "cv.ee",
                "source_site": "cv_ee",
                "salary_min": vacancy.get("salaryFrom"),
                "salary_max": vacancy.get("salaryTo"),
                "salary_currency": "EUR",
                "is_remote": vacancy.get("remoteWork", False),
                "posted_date": vacancy.get("publishDate"),
                "external_id": str(vacancy.get("id", "")),
                "is_active": True
            }
            
            # Определение уровня опыта по заголовку
            title_lower = job_data["title"].lower()
            if any(word in title_lower for word in ["senior", "lead", "principal"]):
                job_data["experience_level"] = "senior"
            elif any(word in title_lower for word in ["junior", "trainee", "intern"]):
                job_data["experience_level"] = "junior"
            elif any(word in title_lower for word in ["middle", "mid"]):
                job_data["experience_level"] = "middle"
            else:
                job_data["experience_level"] = "any"
            
            logger.info(f"Собрана вакансия из JSON: {job_data['title']}")
            return job_data
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге вакансии из JSON: {str(e)}")
            return None

    def _parse_html_jobs(self) -> List[Dict]:
        """Парсинг вакансий из HTML."""
        jobs = []
        try:
            # Ищем карточки вакансий
            job_cards = self._wait_and_find_elements(By.CSS_SELECTOR, "[data-testid='vacancy-item']")
            
            if not job_cards:
                # Альтернативные селекторы
                job_cards = self._wait_and_find_elements(By.CSS_SELECTOR, ".vacancy-item, .job-card, [class*='vacancy']")
            
            logger.info(f"Найдено {len(job_cards)} карточек вакансий в HTML")
            
            for card in job_cards:
                try:
                    job_data = self._parse_job_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Ошибка при парсинге карточки вакансии: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка при парсинге HTML вакансий: {str(e)}")
            
        return jobs

    def _parse_job_card(self, card) -> Optional[Dict]:
        """Парсинг отдельной карточки вакансии."""
        try:
            # Заголовок вакансии
            title_selectors = [
                "h2 a", "h3 a", ".vacancy-title a", "[data-testid='vacancy-title'] a",
                "a[href*='/vacancy/']", ".job-title a"
            ]
            title_element = None
            job_url = ""
            
            for selector in title_selectors:
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, selector)
                    if title_element:
                        job_url = title_element.get_attribute("href")
                        break
                except:
                    continue
            
            if not title_element:
                return None
                
            title = title_element.text.strip()
            
            # Компания
            company_selectors = [
                ".vacancy-company", ".employer-name", "[data-testid='employer-name']",
                ".company-name", ".job-company"
            ]
            company = ""
            for selector in company_selectors:
                try:
                    company_element = card.find_element(By.CSS_SELECTOR, selector)
                    company = company_element.text.strip()
                    break
                except:
                    continue
            
            # Локация
            location_selectors = [
                ".vacancy-location", ".location", "[data-testid='location']",
                ".job-location"
            ]
            location = "Tallinn"  # По умолчанию
            for selector in location_selectors:
                try:
                    location_element = card.find_element(By.CSS_SELECTOR, selector)
                    location = location_element.text.strip()
                    break
                except:
                    continue
            
            # Описание
            description_selectors = [
                ".vacancy-description", ".job-description", "[data-testid='description']"
            ]
            description = ""
            for selector in description_selectors:
                try:
                    desc_element = card.find_element(By.CSS_SELECTOR, selector)
                    description = desc_element.text.strip()
                    break
                except:
                    continue

            job_data = {
                "title": title,
                "company_name": company,
                "location": location,
                "source_url": job_url,
                "description": description,
                "source_site": "cv_ee",
                "salary_currency": "EUR",
                "is_remote": False,
                "is_active": True,
                "experience_level": "any"
            }
            
            # Определение уровня опыта
            title_lower = title.lower()
            if any(word in title_lower for word in ["senior", "lead", "principal"]):
                job_data["experience_level"] = "senior"
            elif any(word in title_lower for word in ["junior", "trainee", "intern"]):
                job_data["experience_level"] = "junior"
            elif any(word in title_lower for word in ["middle", "mid"]):
                job_data["experience_level"] = "middle"
            
            logger.info(f"Собрана вакансия из HTML: {title}")
            return job_data
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге карточки: {str(e)}")
            return None

    def _go_to_next_page(self) -> bool:
        """Переход на следующую страницу."""
        try:
            # Ищем кнопку "Следующая страница"
            next_selectors = [
                "button[aria-label='Next page']",
                ".pagination-next:not(.disabled)",
                "[data-testid='next-page']",
                "a[rel='next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self._wait_and_find_element(By.CSS_SELECTOR, selector, timeout=3)
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при переходе на следующую страницу: {str(e)}")
            return False

    def get_job_details(self, job_url: str) -> Dict:
        """
        Получение детальной информации о вакансии.
        :param job_url: URL вакансии.
        :return: Словарь с детальной информацией о вакансии.
        """
        details = {}
        try:
            self.driver.get(job_url)
            logger.info(f"Открыта страница вакансии: {job_url}")

            # Ожидание загрузки страницы
            time.sleep(2)
            
            # Извлечение детальной информации
            description_selectors = [
                ".vacancy-description", ".job-description", 
                "[data-testid='vacancy-description']", ".content"
            ]
            
            for selector in description_selectors:
                try:
                    description_element = self._wait_and_find_element(By.CSS_SELECTOR, selector, timeout=5)
                    if description_element:
                        details["description"] = description_element.text.strip()
                        break
                except:
                    continue
            
            # Дополнительные данные
            try:
                salary_element = self.driver.find_element(By.CSS_SELECTOR, ".salary, .wage, [data-testid='salary']")
                details["salary"] = salary_element.text.strip()
            except:
                pass

            try:
                employment_type_element = self.driver.find_element(By.CSS_SELECTOR, ".employment-type, [data-testid='employment-type']")
                details["employment_type"] = employment_type_element.text.strip()
            except:
                pass

            logger.info(f"Собрана детальная информация о вакансии: {job_url}")

        except Exception as e:
            logger.error(f"Ошибка при получении деталей вакансии: {str(e)}")
        
        return details

    def close(self):
        """Закрытие браузера."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("Браузер закрыт") 