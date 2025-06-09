import requests
from bs4 import BeautifulSoup
from datetime import datetime

def cvkeskus_scraper(url):
    jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(response.text[:500])  # Debug: print first 500 chars
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all job cards
    job_cards = soup.find_all('div', class_='job-offer-card')
    for card in job_cards:
        title_tag = card.find('a', class_='job-offer__title')
        company_tag = card.find('a', class_='job-offer__company')
        location_tag = card.find('span', class_='job-offer__location')
        salary_tag = card.find('span', class_='job-offer__salary')
        date_tag = card.find('span', class_='job-offer__date')
        desc_tag = card.find('div', class_='job-offer__description')

        title = title_tag.text.strip() if title_tag else None
        company = company_tag.text.strip() if company_tag else None
        location = location_tag.text.strip() if location_tag else None
        salary = salary_tag.text.strip() if salary_tag else None
        publish_date = date_tag.text.strip() if date_tag else None
        description = desc_tag.text.strip() if desc_tag else None
        job_url = title_tag['href'] if title_tag and title_tag.has_attr('href') else None

        # Parse salary if possible
        salary_from, salary_to = None, None
        if salary:
            import re
            match = re.search(r'(\d+[\s\d]*)', salary.replace(',', ''))
            if match:
                salary_from = int(match.group(1).replace(' ', ''))

        # Parse publish date if possible (fallback to today)
        try:
            pub_date = datetime.strptime(publish_date, '%d.%m.%Y') if publish_date else datetime.now()
        except Exception:
            pub_date = datetime.now()

        jobs.append({
            'title': title,
            'company': company,
            'location': location,
            'salaryFrom': salary_from,
            'salaryTo': salary_to,
            'remoteWork': False,  # CV Keskus does not always specify
            'publishDate': pub_date,
            'expirationDate': None,  # Not always available
            'description': description,
            'url': job_url,
            'employerId': hash(company) if company else None  # Use hash as a fallback
        })
    return jobs 