import time
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class CVeeScraper:
    BASE_URL = "https://www.cv.ee/et/vacancies"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'et-EE,et;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.HEADERS)

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
                
                response = self.session.get(self.BASE_URL, params=params)
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
            response = self.session.get(job_url)
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