from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from django.utils import timezone
from ..models import Job, Company
import time

class CVKeskusSeleniumScraper:
    BASE_URL = 'https://www.cvkeskus.ee/toopakkumised'

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    def scrape_jobs(self):
        self.driver.get(self.BASE_URL)
        time.sleep(5)  # Дать странице прогрузиться
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        job_cards = soup.find_all('article', class_='bg-white')
        jobs_created = 0
        for card in job_cards:
            try:
                # Title
                h2 = card.find('h2')
                title = h2.text.strip() if h2 else ''
                # URL
                a_tag = card.find('a', attrs={'data-event-skip-all': True})
                job_url = a_tag['data-href'] if a_tag and a_tag.has_attr('data-href') else ''
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://www.cvkeskus.ee{job_url}"
                # Company
                company_span = card.find('span', class_='job-company')
                company_name = company_span.text.strip() if company_span else ''
                # Location (можно доработать по необходимости)
                location = ''
                # Description (можно доработать по необходимости)
                description = ''
                company, _ = Company.objects.get_or_create(
                    name=company_name or 'Unknown',
                    defaults={'location': location, 'size': 'small'}
                )
                job, created = Job.objects.get_or_create(
                    source_url=job_url,
                    defaults={
                        'title': title,
                        'company': company,
                        'company_name': company_name,
                        'location': location,
                        'description': description,
                        'salary_min': None,
                        'salary_max': None,
                        'salary_currency': 'EUR',
                        'source_site': 'cvkeskus',
                        'posted_date': timezone.now(),
                        'is_active': True
                    }
                )
                if created:
                    jobs_created += 1
            except Exception as e:
                print(f"Error processing job card: {e}")
                continue
        self.driver.quit()
        return jobs_created 