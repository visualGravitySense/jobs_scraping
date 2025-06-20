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
            # Попробуем разные селекторы для заголовка
            title_element = (
                job_card.find('h3', class_='base-search-card__title') or
                job_card.find('a', class_='base-card__full-link') or
                job_card.find('h3') or
                job_card.find('a')
            )
            title = title_element.get_text(strip=True) if title_element else 'Unknown Title'
            
            # Попробуем разные селекторы для компании
            company_element = (
                job_card.find('h4', class_='base-search-card__subtitle') or
                job_card.find('a', class_='hidden-nested-link') or
                job_card.find('h4') or
                job_card.find('span', class_='job-search-card__subtitle-link')
            )
            company = company_element.get_text(strip=True) if company_element else 'Unknown Company'
            
            # Попробуем разные селекторы для локации
            location_element = (
                job_card.find('span', class_='job-search-card__location') or
                job_card.find('div', class_='job-search-card__location') or
                job_card.find('span', string=lambda text: text and ('Estonia' in text or 'Tallinn' in text))
            )
            location = location_element.get_text(strip=True) if location_element else 'Unknown Location'
            
            # Get job URL and clean it
            job_link = job_card.find('a', class_='base-card__full-link') or job_card.find('a')
            job_url = job_link.get('href', '').split('?')[0] if job_link else None  # Убираем параметры из URL
            
            # Убедимся, что URL полный
            if job_url and not job_url.startswith('http'):
                job_url = 'https://www.linkedin.com' + job_url
            
            # Get salary if available
            salary_element = job_card.find('span', class_='job-search-card__salary-info')
            salary_text = salary_element.get_text(strip=True) if salary_element else None
            salary_min, salary_max = self._get_salary_range(salary_text) if salary_text else (None, None)
            
            # Попробуем получить описание из карточки
            description_element = job_card.find('div', class_='job-search-card__snippet')
            description = description_element.get_text(strip=True) if description_element else ''
            
            # Get posting date
            date_element = (
                job_card.find('time', class_='job-search-card__listdate') or
                job_card.find('time', class_='job-posted-date') or
                job_card.find('time')
            )
            posted_date = date_element.get('datetime') if date_element else None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'description': description,
                'posted_date': posted_date,
                'source': 'linkedin'
            }
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None

    def search_jobs(self, keywords: List[str], location: str = None, max_pages: int = 5) -> List[Dict]:
        """Search for jobs on LinkedIn"""
        all_jobs = []
        seen_urls = set()  # Для дедупликации по URL
        seen_signatures = set()  # Для дедупликации по title + company + posted_date
        
        for page in range(max_pages):
            try:
                params = {
                    'keywords': ' '.join(keywords),
                    'location': location or 'Estonia',
                    'start': page * 25,  # LinkedIn shows 25 jobs per page
                }
                
                logger.info(f"Searching LinkedIn page {page + 1} with params: {params}")
                
                response = self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Попробуем разные селекторы для карточек вакансий
                job_cards = (
                    soup.find_all('div', class_='base-card') or
                    soup.find_all('div', class_='job-search-card') or
                    soup.find_all('li', class_='result-card') or
                    soup.find_all('div', class_='base-search-card')
                )
                
                logger.info(f"Found {len(job_cards)} job cards on page {page + 1}")
                
                if not job_cards:
                    logger.warning(f"No job cards found on page {page + 1}")
                    break
                
                for card in job_cards:
                    job_data = self._parse_job_card(card)
                    if job_data and job_data.get('title') != 'Unknown Title':
                        # Получаем дату публикации
                        date_element = card.find('time', class_='job-search-card__listdate') or \
                                     card.find('time', class_='job-posted-date') or \
                                     card.find('time')
                        posted_date = date_element.get('datetime') if date_element else ''
                        
                        # Создаем уникальную сигнатуру вакансии
                        job_signature = f"{job_data.get('title', '')}-{job_data.get('company', '')}-{posted_date}"
                        job_url = job_data.get('url')
                        
                        # Проверяем дубликаты по URL и сигнатуре
                        is_duplicate = False
                        if job_url:
                            is_duplicate = job_url in seen_urls
                            if not is_duplicate:
                                seen_urls.add(job_url)
                        
                        if not is_duplicate:
                            is_duplicate = job_signature in seen_signatures
                            if not is_duplicate:
                                seen_signatures.add(job_signature)
                                job_data['posted_date'] = posted_date
                                all_jobs.append(job_data)
                
                # Respect rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching jobs on page {page}: {str(e)}")
                break
        
        logger.info(f"Total unique jobs found: {len(all_jobs)}")
        return all_jobs

    def get_job_details(self, job_url: str) -> Dict:
        """Get detailed information about a specific job"""
        try:
            response = self.session.get(job_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job description
            description_selectors = [
                'div.show-more-less-html__markup',
                'div.description__text',
                'div.jobs-description-content__text',
                'div.jobs-box__html-content'
            ]
            
            description = ''
            for selector in description_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    description = desc_element.get_text(strip=True)
                    break
            
            # Extract additional details
            details = {
                'description': description,
                'posted_date': None,
                'employment_type': None,
                'experience_level': None
            }
            
            # Try to get posting date
            date_selectors = [
                'span.posted-time-ago__text',
                'time.job-posted-date',
                'span.jobs-unified-top-card__posted-date'
            ]
            
            for selector in date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    details['posted_date'] = date_element.get_text(strip=True)
                    break
            
            # Try to get employment type
            employment_selectors = [
                'span.job-criteria-item__text',
                'li.jobs-unified-top-card__job-insight span'
            ]
            
            for selector in employment_selectors:
                employment_element = soup.select_one(selector)
                if employment_element:
                    details['employment_type'] = employment_element.get_text(strip=True)
                    break
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting job details from {job_url}: {str(e)}")
            return {
                'description': '',
                'posted_date': None,
                'employment_type': None,
                'experience_level': None
            } 