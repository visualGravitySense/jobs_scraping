from celery import shared_task
from django.core.management import call_command

@shared_task
def scrape_cv_ee_jobs():
    """Task to scrape jobs from cv.ee"""
    try:
        call_command('scrape_cv_ee')
        return "Successfully scraped jobs from cv.ee"
    except Exception as e:
        return f"Error scraping jobs from cv.ee: {str(e)}"

@shared_task
def scrape_linkedin_jobs():
    """Task to scrape jobs from LinkedIn"""
    try:
        call_command('scrape_linkedin')
        return "Successfully scraped jobs from LinkedIn"
    except Exception as e:
        return f"Error scraping jobs from LinkedIn: {str(e)}" 