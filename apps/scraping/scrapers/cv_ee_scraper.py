import time
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone
from ..models import Job, Company

logger = logging.getLogger(__name__)

class CVeeScraper:
    BASE_URL = 'https://www.cv.ee/et/vacancies'
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_salary_range(self, salary_text: str) -> tuple:
        """Extract salary range from text"""
        try:
            # Remove currency symbols and convert to numbers
            salary_text = salary_text.replace('€', '').replace('$', '').replace(',', '')
            if '-' in salary_text:
                min_salary, max_salary = salary_text.split('-')
                return (
                    int(min_salary.strip()),
                    int(max_salary.strip())
                )
            return (int(salary_text.strip()), None)
        except (ValueError, AttributeError):
            return (None, None)

    def _parse_job_card(self, job_card) -> Dict:
        """Parse a single job card from cv.ee"""
        try:
            # Get job title and URL
            title_element = job_card.find('h2', class_='vacancy-title')
            title = title_element.text.strip() if title_element else ''
            job_url = title_element.find('a')['href'] if title_element else None
            if job_url and not job_url.startswith('http'):
                job_url = f"https://www.cv.ee{job_url}"
            
            # Get company name
            company_element = job_card.find('div', class_='vacancy-company')
            company = company_element.text.strip() if company_element else ''
            
            # Get location
            location_element = job_card.find('div', class_='vacancy-location')
            location = location_element.text.strip() if location_element else ''
            
            # Get salary
            salary_element = job_card.find('div', class_='vacancy-salary')
            salary_text = salary_element.text.strip() if salary_element else None
            salary_min, salary_max = self._get_salary_range(salary_text) if salary_text else (None, None)
            
            # Get job description
            description_element = job_card.find('div', class_='vacancy-description')
            description = description_element.text.strip() if description_element else ''
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'description': description,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'source': 'cv.ee'
            }
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None

    def search_jobs(self, keywords: List[str] = None, location: str = None, max_pages: int = 5) -> List[Dict]:
        """Search for jobs on cv.ee"""
        all_jobs = []
        
        for page in range(max_pages):
            try:
                params = {
                    'query': ' '.join(keywords) if keywords else '',
                    'location': location,
                    'page': page + 1
                }
                
                url = f"{self.BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
                logger.info(f"Searching jobs with URL: {url}")
                logger.info(f"Request parameters: {params}")
                
                response = requests.get(self.BASE_URL, params=params, headers=self.headers)
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                logger.info(f"Response URL: {response.url}")
                
                if response.status_code != 200:
                    logger.error(f"Error response content: {response.text[:500]}")
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='vacancy-card')
                
                logger.info(f"Found {len(job_cards)} job cards on page {page + 1}")
                
                if not job_cards:
                    logger.info(f"No jobs found on page {page + 1}")
                    break
                
                for card in job_cards:
                    job_data = self._parse_job_card(card)
                    if job_data:
                        all_jobs.append(job_data)
                
                # Respect rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching jobs on page {page}: {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Response content: {e.response.text[:500]}")
                break
        
        return all_jobs

    def get_job_details(self, job_url: str) -> Dict:
        """Get detailed information about a specific job"""
        try:
            response = requests.get(job_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job description
            description = soup.find('div', class_='vacancy-description')
            description_text = description.text.strip() if description else ''
            
            # Extract additional details
            details = {
                'description': description_text,
                'posted_date': None,
                'employment_type': None,
                'experience_level': None
            }
            
            # Try to get posting date
            date_element = soup.find('div', class_='vacancy-date')
            if date_element:
                details['posted_date'] = date_element.text.strip()
            
            # Try to get employment type
            employment_element = soup.find('div', class_='vacancy-employment-type')
            if employment_element:
                details['employment_type'] = employment_element.text.strip()
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting job details from {job_url}: {str(e)}")
            return None

    def scrape_jobs(self):
        try:
            response = requests.get(self.BASE_URL, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('li', class_='vacancies-list__item')
            
            jobs_created = 0
            for card in job_cards:
                try:
                    # Title and URL
                    title_tag = card.find('a', class_='vacancy-item__title')
                    title = title_tag.text.strip() if title_tag else ''
                    job_url = title_tag['href'] if title_tag else ''
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.cv.ee{job_url}"

                    # Company (ищем в info-secondary или других блоках)
                    company_name = ''
                    info_secondary = card.find('div', class_='vacancy-item__info-secondary')
                    if info_secondary:
                        company_name = info_secondary.text.strip().split('\n')[0]

                    # Location (может быть в info или info-secondary)
                    location = ''
                    info = card.find('div', class_='vacancy-item__info')
                    if info:
                        location = info.text.strip().split('\n')[0]

                    # Description (body)
                    description = ''
                    body = card.find('div', class_='vacancy-item__body')
                    if body:
                        description = body.text.strip()

                    # Salary (если есть)
                    salary = ''
                    # Можно добавить парсинг зарплаты, если найдете где она в html

                    # Get or create company
                    company, _ = Company.objects.get_or_create(
                        name=company_name or 'Unknown',
                        defaults={
                            'location': location,
                            'size': 'small'
                        }
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
                            'source_site': 'cv_ee',
                            'posted_date': timezone.now(),
                            'is_active': True
                        }
                    )
                    if created:
                        jobs_created += 1
                except Exception as e:
                    logger.error(f"Error processing job card: {e}")
                    continue
            return jobs_created
        except Exception as e:
            logger.error(f"Error scraping cv.ee: {e}")
            return 0 