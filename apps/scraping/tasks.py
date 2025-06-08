from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
import logging
import subprocess
import os

logger = logging.getLogger(__name__)

@shared_task
def scrape_cv_keskus():
    """
    Scrape CV Keskus jobs and import them into the database
    """
    try:
        logger.info("Starting CV Keskus scraping task")
        
        # Run the CV Keskus scraper
        script_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'cvkeskus_selenium.py')
        result = subprocess.run(['python', script_path], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            logger.error(f"CV Keskus scraper failed: {result.stderr}")
            return f"Scraping failed: {result.stderr}"
        
        logger.info("CV Keskus scraping completed successfully")
        
        # Import the scraped data
        call_command('import_parsed_jobs')
        logger.info("Data import completed successfully")
        
        return "CV Keskus scraping and import completed successfully"
        
    except Exception as e:
        logger.error(f"Error in CV Keskus scraping task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def scrape_all_sources():
    """
    Scrape all configured job sources
    """
    try:
        logger.info("Starting comprehensive job scraping task")
        results = []
        
        # Scrape CV Keskus
        cv_result = scrape_cv_keskus()
        results.append(f"CV Keskus: {cv_result}")
        
        # Add other scrapers here as they're implemented
        # linkedin_result = scrape_linkedin()
        # results.append(f"LinkedIn: {linkedin_result}")
        
        logger.info("All scraping tasks completed")
        return "; ".join(results)
        
    except Exception as e:
        logger.error(f"Error in comprehensive scraping task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def cleanup_old_jobs():
    """
    Clean up expired job postings
    """
    try:
        from .models import ParsedJob
        
        # Delete jobs that expired more than 30 days ago
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        deleted_count = ParsedJob.objects.filter(
            expiration_date__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} expired job postings")
        return f"Cleaned up {deleted_count} expired job postings"
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def generate_job_analytics():
    """
    Generate and cache job market analytics
    """
    try:
        from .models import ParsedJob, ParsedCompany
        from django.db.models import Count, Avg
        
        # Calculate basic statistics
        total_jobs = ParsedJob.objects.count()
        remote_jobs = ParsedJob.objects.filter(remote_work=True).count()
        companies_count = ParsedCompany.objects.count()
        
        # Calculate average salary
        avg_salary = ParsedJob.objects.filter(
            salary_from__isnull=False
        ).aggregate(avg_salary=Avg('salary_from'))['avg_salary']
        
        logger.info(f"Analytics generated: {total_jobs} jobs, {remote_jobs} remote, {companies_count} companies")
        
        # You could store these in cache or database for quick access
        return {
            'total_jobs': total_jobs,
            'remote_jobs': remote_jobs,
            'companies_count': companies_count,
            'avg_salary': avg_salary,
            'generated_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analytics generation: {str(e)}")
        return f"Error: {str(e)}" 