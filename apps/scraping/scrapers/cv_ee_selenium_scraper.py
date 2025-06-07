import time
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

logger = logging.getLogger(__name__)

class CVeeSeleniumScraper:
    BASE_URL = "https://www.cv.ee/et/vacancies"

    def __init__(self, headless: bool = True):
        """
        Инициализация Selenium-парсера для cv.ee.
        :param headless: Запускать браузер в фоновом режиме (без GUI).
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Использование webdriver-manager для автоматической установки ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def _wait_and_find_element(self, by: By, value: str):
        """Ожидание и поиск элемента с обработкой ошибок."""
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.error(f"Элемент не найден: {value}")
            return None

    def _wait_and_find_elements(self, by: By, value: str):
        """Ожидание и поиск элементов с обработкой ошибок."""
        try:
            elements = self.wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except TimeoutException:
            logger.error(f"Элементы не найдены: {value}")
            return []

    def search_jobs(self, keywords: List[str] = None, location: str = None, max_pages: int = 3) -> List[Dict]:
        """
        Поиск вакансий на cv.ee с помощью Selenium.
        :param keywords: Список ключевых слов для поиска.
        :param location: Локация для поиска.
        :param max_pages: Максимальное количество страниц для парсинга.
        :return: Список словарей с данными о вакансиях.
        """
        all_jobs = []
        try:
            self.driver.get(self.BASE_URL)
            logger.info(f"Открыта страница: {self.BASE_URL}")

            # Ожидание загрузки страницы
            keyword_input = self._wait_and_find_element(By.CSS_SELECTOR, "input[type='text']")
            if not keyword_input:
                return all_jobs

            # Ввод ключевых слов
            if keywords:
                keyword_input.clear()
                keyword_input.send_keys(" ".join(keywords))
                logger.info(f"Введены ключевые слова: {keywords}")

            # Ввод локации
            if location:
                location_input = self._wait_and_find_element(By.CSS_SELECTOR, "input[placeholder*='Asukoht']")
                if location_input:
                    location_input.clear()
                    location_input.send_keys(location)
                    logger.info(f"Введена локация: {location}")

            # Запуск поиска
            search_button = self._wait_and_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if search_button:
                search_button.click()
                logger.info("Запущен поиск вакансий")

            # Парсинг страниц
            for page in range(max_pages):
                logger.info(f"Парсинг страницы {page + 1}")
                
                # Ожидание загрузки результатов
                job_cards = self._wait_and_find_elements(By.CSS_SELECTOR, ".vacancy-card")
                if not job_cards:
                    logger.info("Вакансии не найдены")
                    break

                logger.info(f"Найдено {len(job_cards)} вакансий на странице {page + 1}")

                # Сбор данных о вакансиях
                for card in job_cards:
                    try:
                        title = card.find_element(By.CSS_SELECTOR, "h2.vacancy-title").text.strip()
                        company = card.find_element(By.CSS_SELECTOR, "div.vacancy-company").text.strip()
                        location = card.find_element(By.CSS_SELECTOR, "div.vacancy-location").text.strip()
                        job_url = card.find_element(By.CSS_SELECTOR, "h2.vacancy-title a").get_attribute("href")
                        description = card.find_element(By.CSS_SELECTOR, "div.vacancy-description").text.strip()

                        job_data = {
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": job_url,
                            "description": description,
                            "source": "cv.ee"
                        }
                        all_jobs.append(job_data)
                        logger.info(f"Собрана вакансия: {title}")
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        logger.error(f"Ошибка при парсинге вакансии: {str(e)}")
                        continue

                # Проверка наличия следующей страницы
                next_button = self._wait_and_find_element(By.CSS_SELECTOR, "a.pagination-next:not(.disabled)")
                if not next_button:
                    logger.info("Достигнут конец списка вакансий")
                    break

                # Переход на следующую страницу
                next_button.click()
                time.sleep(2)  # Пауза для загрузки новой страницы

        except Exception as e:
            logger.error(f"Ошибка при поиске вакансий: {str(e)}")
        finally:
            self.driver.quit()
            logger.info("Браузер закрыт")

        return all_jobs

    def get_job_details(self, job_url: str) -> Dict:
        """
        Получение детальной информации о вакансии.
        :param job_url: URL вакансии.
        :return: Словарь с детальной информацией о вакансии.
        """
        try:
            self.driver.get(job_url)
            logger.info(f"Открыта страница вакансии: {job_url}")

            # Ожидание загрузки страницы
            description_element = self._wait_and_find_element(By.CSS_SELECTOR, "div.vacancy-description")
            if not description_element:
                return {}

            # Извлечение детальной информации
            description = description_element.text.strip()
            
            # Попытка получить дополнительные данные
            try:
                posted_date = self.driver.find_element(By.CSS_SELECTOR, "div.vacancy-date").text.strip()
            except NoSuchElementException:
                posted_date = None

            try:
                employment_type = self.driver.find_element(By.CSS_SELECTOR, "div.vacancy-employment-type").text.strip()
            except NoSuchElementException:
                employment_type = None

            try:
                salary = self.driver.find_element(By.CSS_SELECTOR, "div.vacancy-salary").text.strip()
            except NoSuchElementException:
                salary = None

            details = {
                "description": description,
                "posted_date": posted_date,
                "employment_type": employment_type,
                "salary": salary
            }
            logger.info(f"Собрана детальная информация о вакансии: {job_url}")

        except Exception as e:
            logger.error(f"Ошибка при получении деталей вакансии: {str(e)}")
            details = {}
        finally:
            self.driver.quit()
            logger.info("Браузер закрыт")

        return details 