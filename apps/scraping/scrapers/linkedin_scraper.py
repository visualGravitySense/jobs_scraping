import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)

class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs/search"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.HEADERS)
        self._setup_auth()

    def _setup_auth(self):
        """Setup authentication for LinkedIn"""
        # TODO: Implement proper authentication
        # For now, we'll use public access
        pass

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
        """Parse a single job card from LinkedIn"""
        try:
            title = job_card.find('h3', class_='base-search-card__title').text.strip()
            company = job_card.find('h4', class_='base-search-card__subtitle').text.strip()
            location = job_card.find('span', class_='job-search-card__location').text.strip()
            
            # Get job URL
            job_link = job_card.find('a', class_='base-card__full-link')
            job_url = job_link['href'] if job_link else None
            
            # Get salary if available
            salary_element = job_card.find('span', class_='job-search-card__salary-info')
            salary_text = salary_element.text.strip() if salary_element else None
            salary_min, salary_max = self._get_salary_range(salary_text) if salary_text else (None, None)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'source': 'linkedin'
            }
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None

    def search_jobs(self, keywords: List[str], location: str = None, max_pages: int = 5) -> List[Dict]:
        """Search for jobs on LinkedIn"""
        all_jobs = []
        
        for page in range(max_pages):
            try:
                params = {
                    'keywords': ' '.join(keywords),
                    'location': location,
                    'start': page * 25,  # LinkedIn shows 25 jobs per page
                }
                
                response = self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')
                
                if not job_cards:
                    break
                
                for card in job_cards:
                    job_data = self._parse_job_card(card)
                    if job_data:
                        all_jobs.append(job_data)
                
                # Respect rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching jobs on page {page}: {str(e)}")
                break
        
        return all_jobs

    def get_job_details(self, job_url: str) -> Dict:
        """Get detailed information about a specific job"""
        try:
            response = self.session.get(job_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job description
            description = soup.find('div', class_='show-more-less-html__markup')
            description_text = description.text.strip() if description else ''
            
            # Extract additional details
            details = {
                'description': description_text,
                'posted_date': None,
                'employment_type': None,
                'experience_level': None
            }
            
            # Try to get posting date
            date_element = soup.find('span', class_='posted-time-ago__text')
            if date_element:
                details['posted_date'] = date_element.text.strip()
            
            # Try to get employment type
            employment_element = soup.find('span', class_='job-criteria-item__text')
            if employment_element:
                details['employment_type'] = employment_element.text.strip()
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting job details from {job_url}: {str(e)}")
            return None 