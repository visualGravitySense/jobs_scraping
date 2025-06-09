from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time

def cvkeskus_selenium_scraper(url, headless=True):
    jobs = []
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait for job cards to load
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.cursor-pointer.shadow'))
        )
        time.sleep(2)  # Give time for all jobs to load
    except Exception as e:
        print(f"Timeout waiting for job cards: {e}")

    # job_cards = driver.find_elements(By.CSS_SELECTOR, 'div.cursor-pointer.shadow')
    job_cards = driver.find_elements(By.CSS_SELECTOR, 'article[id^=\"jobad_\"]')
    print(f"[DEBUG] Found {len(job_cards)} job cards on the page.")
    if job_cards:
        try:
            print(f"[DEBUG] First job card outer HTML: {job_cards[0].get_attribute('outerHTML')}")
        except Exception as e:
            print(f"[DEBUG] Could not get outer HTML of first job card: {e}")

    for idx, card in enumerate(job_cards):
        try:
            # Initialize all fields with defaults
            title = company = location = salary = publish_date = description = job_url = None
            
            # Try to extract title and URL (usually in an <a> tag)
            try:
                title_tag = card.find_element(By.CSS_SELECTOR, 'a')
                title = title_tag.text.strip()
                job_url = title_tag.get_attribute('href')
            except:
                try:
                    title_tag = card.find_element(By.TAG_NAME, 'a')
                    title = title_tag.text.strip()
                    job_url = title_tag.get_attribute('href')
                except:
                    print(f"[DEBUG] Could not find title for job card #{idx}")
            
            # Try to extract company (usually in a span or div)
            try:
                company_tag = card.find_element(By.CSS_SELECTOR, 'span.font-semibold')
                company = company_tag.text.strip()
            except:
                try:
                    # Try alternative selectors
                    company_spans = card.find_elements(By.TAG_NAME, 'span')
                    for span in company_spans:
                        if span.text.strip() and len(span.text.strip()) > 3:
                            company = span.text.strip()
                            break
                except:
                    print(f"[DEBUG] Could not find company for job card #{idx}")
            
            # Try to extract location
            try:
                location_tag = card.find_element(By.CSS_SELECTOR, 'span.text-sm')
                location = location_tag.text.strip()
            except:
                try:
                    # Try to find any span containing location-like text
                    spans = card.find_elements(By.TAG_NAME, 'span')
                    for span in spans:
                        text = span.text.strip()
                        if any(word in text.lower() for word in ['tallinn', 'tartu', 'estonia', 'eesti', 'kaugtöö']):
                            location = text
                            break
                except:
                    location = "Estonia"  # Default location
            
            # Try to extract salary
            try:
                salary_tag = card.find_elements(By.XPATH, ".//span[contains(text(),'€')]")
                salary = salary_tag[0].text.strip() if salary_tag else None
            except:
                try:
                    # Look for any text containing € or salary keywords
                    all_text = card.text
                    import re
                    salary_match = re.search(r'(\d+.*€.*\d*)', all_text)
                    salary = salary_match.group(1) if salary_match else None
                except:
                    pass
            
            # Try to extract date
            try:
                date_tag = card.find_element(By.CSS_SELECTOR, 'span.text-xs')
                publish_date = date_tag.text.strip()
            except:
                publish_date = datetime.now().strftime('%d.%m.%Y')
            
            # Try to extract description
            try:
                desc_tag = card.find_element(By.CSS_SELECTOR, 'div.line-clamp-2')
                description = desc_tag.text.strip()
            except:
                try:
                    # Use the full text of the card as description
                    description = card.text.strip()[:500]  # Limit to 500 chars
                except:
                    description = "No description available"

            # Skip if we don't have at least title and company
            if not title or not company:
                print(f"[DEBUG] Skipping job card #{idx} - missing title or company")
                continue

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

            print(f"[DEBUG] Successfully parsed job #{idx}: {title} at {company}")
            
            jobs.append({
                'title': title,
                'company': company,
                'location': location or "Estonia",
                'salaryFrom': salary_from,
                'salaryTo': salary_to,
                'remoteWork': False,  # CV Keskus does not always specify
                'publishDate': pub_date,
                'expirationDate': None,  # Not always available
                'description': description,
                'url': job_url,
                'employerId': hash(company) if company else None  # Use hash as a fallback
            })
        except Exception as e:
            print(f"[DEBUG] Error parsing job card #{idx}: {e}")
    driver.quit()
    return jobs 