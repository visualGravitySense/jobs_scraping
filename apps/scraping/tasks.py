from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
from django.db import transaction
from django.conf import settings
import logging
import subprocess
import os
import requests
from typing import List, Dict
# import redis  # Redis отключен для разработки
import time
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@shared_task
def scrape_cv_ee_jobs():
    """
    Scrape CV.ee jobs and import them into the database
    """
    def set_progress(scraper_name, percent):
        pass  # Redis отключен для разработки

    try:
        logger.info("Starting CV.ee scraping task")
        
        from .scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper
        from .models import Job, Company
        
        scraper = CVeeSeleniumScraper()
        jobs_data = scraper.search_jobs(
            keywords=["python", "django", "javascript", "react", "vue", "angular", "node.js"],
            location="Tallinn",
            max_pages=3
        )
        
        imported_count = 0
        updated_count = 0
        total = len(jobs_data) if jobs_data else 1
        
        with transaction.atomic():
            for i, job_data in enumerate(jobs_data):
                try:
                    # Создаем или получаем компанию
                    company = None
                    if job_data.get('company'):
                        company, created = Company.objects.get_or_create(
                            name=job_data['company'],
                            defaults={'location': job_data.get('location', '')}
                        )
                    
                    # Создаем или обновляем вакансию
                    job, created = Job.objects.update_or_create(
                        source_url=job_data['source_url'],
                        defaults={
                            'title': job_data['title'],
                            'company': company,
                            'company_name': job_data.get('company', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description', ''),
                            'requirements': job_data.get('requirements', ''),
                            'source_site': 'cv_ee',
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'salary_currency': job_data.get('salary_currency', 'EUR'),
                            'is_remote': job_data.get('is_remote', False),
                            'experience_level': job_data.get('experience_level', 'any'),
                            'employment_type': job_data.get('employment_type'),
                            'posted_date': job_data.get('posted_date'),
                            'is_active': True
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
                    continue
                set_progress('cvee', int((i + 1) / total * 100))
        
        set_progress('cvee', 100)
        logger.info(f"CV.ee scraping completed: {imported_count} new, {updated_count} updated")
        
        # Запускаем расчет скоров для новых вакансий
        # calculate_job_scores.delay()  # Celery отключен для разработки
        
        return f"CV.ee scraping completed: {imported_count} new jobs, {updated_count} updated"
        
    except Exception as e:
        logger.error(f"Error in CV.ee scraping task: {str(e)}")
        set_progress('cvee', 0)
        return f"Error: {str(e)}"

@shared_task
def scrape_linkedin_jobs():
    """
    Scrape LinkedIn jobs and import them into the database
    """
    def set_progress(scraper_name, percent):
        pass  # Redis отключен для разработки

    try:
        logger.info("Starting LinkedIn scraping task")
        
        from .scrapers.linkedin_scraper import LinkedInScraper
        from .models import Job, Company, LinkedInAuth
        
        # Получаем активные учетные данные LinkedIn
        linkedin_auth = LinkedInAuth.objects.filter(is_active=True).first()
        if not linkedin_auth:
            logger.warning("No active LinkedIn credentials found")
            set_progress('linkedin', 0)
            return "No LinkedIn credentials available"
        
        scraper = LinkedInScraper()
        jobs_data = scraper.search_jobs(
            keywords=["software engineer", "developer", "programmer"],
            location="Estonia",
            max_pages=3
        )
        
        imported_count = 0
        updated_count = 0
        total = len(jobs_data) if jobs_data else 1
        
        with transaction.atomic():
            for i, job_data in enumerate(jobs_data):
                try:
                    # Создаем или получаем компанию
                    company = None
                    if job_data.get('company'):
                        company, created = Company.objects.get_or_create(
                            name=job_data['company'],
                            defaults={'location': job_data.get('location', '')}
                        )
                    
                    # Создаем или обновляем вакансию
                    job, created = Job.objects.update_or_create(
                        source_url=job_data['url'],
                        defaults={
                            'title': job_data['title'],
                            'company': company,
                            'company_name': job_data.get('company', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description', ''),
                            'source_site': 'linkedin',
                            'is_remote': job_data.get('is_remote', False),
                            'experience_level': job_data.get('experience_level', 'any'),
                            'is_active': True
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing LinkedIn job {job_data.get('title', 'Unknown')}: {str(e)}")
                    continue
                set_progress('linkedin', int((i + 1) / total * 100))
        
        set_progress('linkedin', 100)
        logger.info(f"LinkedIn scraping completed: {imported_count} new, {updated_count} updated")
        
        # Запускаем расчет скоров для новых вакансий
        # calculate_job_scores.delay()  # Celery отключен для разработки
        
        return f"LinkedIn scraping completed: {imported_count} new jobs, {updated_count} updated"
        
    except Exception as e:
        logger.error(f"Error in LinkedIn scraping task: {str(e)}")
        set_progress('linkedin', 0)
        return f"Error: {str(e)}"

@shared_task
def scrape_cvkeskus_jobs():
    """
    Scrape CVKeskus jobs and import them into the database
    """
    def set_progress(scraper_name, percent):
        pass  # Redis отключен для разработки

    try:
        logger.info("Starting CVKeskus scraping task")
        
        from .scrapers.cvkeskus_scraper import CVKeskusScraper
        from .models import Job, Company
        
        scraper = CVKeskusScraper()
        jobs_data = scraper.search_jobs(
            max_pages=3
        )
        
        imported_count = 0
        updated_count = 0
        total = len(jobs_data) if jobs_data else 1
        
        with transaction.atomic():
            for i, job_data in enumerate(jobs_data):
                try:
                    # Создаем или получаем компанию
                    company = None
                    if job_data.get('company'):
                        company, created = Company.objects.get_or_create(
                            name=job_data['company'],
                            defaults={'location': job_data.get('location', '')}
                        )
                    
                    # Создаем или обновляем вакансию
                    job, created = Job.objects.update_or_create(
                        source_url=job_data['url'],
                        defaults={
                            'title': job_data['title'],
                            'company': company,
                            'company_name': job_data.get('company', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description', ''),
                            'source_site': 'cvkeskus',
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'salary_currency': 'EUR',
                            'is_remote': False,  # CVKeskus doesn't provide this info directly
                            'employment_type': job_data.get('employment_type', 'full_time'),
                            'is_active': True
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
                    continue
                set_progress('cvkeskus', int((i + 1) / total * 100))
        
        set_progress('cvkeskus', 100)
        logger.info(f"CVKeskus scraping completed: {imported_count} new, {updated_count} updated")
        
        # Запускаем расчет скоров для новых вакансий
        # calculate_job_scores.delay()  # Celery отключен для разработки
        
        return f"CVKeskus scraping completed: {imported_count} new jobs, {updated_count} updated"
        
    except Exception as e:
        logger.error(f"Error in CVKeskus scraping task: {str(e)}")
        set_progress('cvkeskus', 0)
        return f"Error: {str(e)}"

@shared_task
def scrape_all_sources():
    """
    Scrape all configured job sources
    """
    try:
        logger.info("Starting comprehensive job scraping task")
        results = []
        
        # Scrape CV.ee
        cv_result = scrape_cv_ee_jobs()
        results.append(f"CV.ee: {cv_result}")
        
        # Scrape LinkedIn
        linkedin_result = scrape_linkedin_jobs()
        results.append(f"LinkedIn: {linkedin_result}")
        
        # Scrape CVKeskus
        cvkeskus_result = scrape_cvkeskus_jobs()
        results.append(f"CVKeskus: {cvkeskus_result}")
        
        logger.info("All scraping tasks completed")
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Error in scrape_all_sources task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def calculate_job_scores():
    """
    Calculate relevance scores for all active jobs
    """
    try:
        from .models import Job, JobScore, UserProfile
        from .services import JobScoringService
        
        logger.info("Starting job scoring calculation")
        
        # Получаем все активные вакансии без скоров или с устаревшими скорами
        cutoff_date = timezone.now() - timezone.timedelta(hours=24)
        jobs_to_score = Job.objects.filter(
            is_active=True
        ).exclude(
            jobscore__updated_at__gte=cutoff_date
        )
        
        scoring_service = JobScoringService()
        scored_count = 0
        
        for job in jobs_to_score:
            try:
                # Рассчитываем базовые скоры
                relevance_score = scoring_service.calculate_relevance_score(job)
                skill_match_score = scoring_service.calculate_skill_match_score(job)
                salary_score = scoring_service.calculate_salary_score(job)
                location_score = scoring_service.calculate_location_score(job)
                
                # Создаем или обновляем скор
                job_score, created = JobScore.objects.update_or_create(
                    job=job,
                    defaults={
                        'relevance_score': relevance_score,
                        'skill_match_score': skill_match_score,
                        'salary_score': salary_score,
                        'location_score': location_score,
                        'calculated_at': timezone.now()
                    }
                )
                
                scored_count += 1
                
            except Exception as e:
                logger.error(f"Error scoring job {job.id}: {str(e)}")
                continue
        
        logger.info(f"Job scoring completed: {scored_count} jobs scored")
        return f"Scored {scored_count} jobs"
        
    except Exception as e:
        logger.error(f"Error in job scoring task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def send_job_notifications():
    """
    Send notifications about new relevant jobs to users
    """
    try:
        from .models import Job, UserProfile, Application
        from .services import NotificationService
        
        logger.info("Starting job notifications task")
        
        # Получаем пользователей с включенными уведомлениями
        users_with_notifications = UserProfile.objects.filter(
            is_notifications_enabled=True,
            telegram_chat_id__isnull=False
        ).exclude(telegram_chat_id='')
        
        notification_service = NotificationService()
        sent_count = 0
        
        # Получаем новые вакансии за последние 24 часа
        cutoff_date = timezone.now() - timezone.timedelta(hours=24)
        new_jobs = Job.objects.filter(
            is_active=True,
            created_at__gte=cutoff_date,
            jobscore__relevance_score__gte=70  # Только релевантные вакансии
        ).select_related('jobscore')
        
        for user_profile in users_with_notifications:
            try:
                # Фильтруем вакансии по предпочтениям пользователя
                relevant_jobs = notification_service.filter_jobs_for_user(new_jobs, user_profile)
                
                if relevant_jobs:
                    # Отправляем уведомление
                    success = notification_service.send_telegram_notification(
                        user_profile.telegram_chat_id,
                        relevant_jobs
                    )
                    
                    if success:
                        sent_count += 1
                        
            except Exception as e:
                logger.error(f"Error sending notification to user {user_profile.user.username}: {str(e)}")
                continue
        
        logger.info(f"Job notifications completed: {sent_count} notifications sent")
        return f"Sent {sent_count} notifications"
        
    except Exception as e:
        logger.error(f"Error in job notifications task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def cleanup_old_jobs():
    """
    Clean up expired job postings and inactive data
    """
    try:
        from .models import Job, JobScore, Application
        
        logger.info("Starting cleanup task")
        
        # Деактивируем старые вакансии (старше 60 дней)
        cutoff_date = timezone.now() - timezone.timedelta(days=60)
        deactivated_count = Job.objects.filter(
            created_at__lt=cutoff_date,
            is_active=True
        ).update(is_active=False)
        
        # Удаляем очень старые скоры (старше 90 дней)
        old_scores_cutoff = timezone.now() - timezone.timedelta(days=90)
        deleted_scores = JobScore.objects.filter(
            calculated_at__lt=old_scores_cutoff
        ).delete()[0]
        
        logger.info(f"Cleanup completed: {deactivated_count} jobs deactivated, {deleted_scores} old scores deleted")
        return f"Deactivated {deactivated_count} jobs, deleted {deleted_scores} old scores"
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def generate_job_analytics():
    """
    Generate and cache job market analytics
    """
    try:
        from .models import Job, Company, JobScore
        from django.db.models import Count, Avg, Q
        from django.core.cache import cache
        
        logger.info("Starting analytics generation")
        
        # Базовая статистика
        total_jobs = Job.objects.filter(is_active=True).count()
        remote_jobs = Job.objects.filter(is_active=True, is_remote=True).count()
        companies_count = Company.objects.count()
        
        # Статистика по зарплатам
        salary_stats = Job.objects.filter(
            is_active=True,
            salary_min__isnull=False
        ).aggregate(
            avg_salary=Avg('salary_min'),
            min_salary=Avg('salary_min'),
            max_salary=Avg('salary_max')
        )
        
        # Статистика по уровням опыта
        experience_stats = Job.objects.filter(is_active=True).values('experience_level').annotate(
            count=Count('id')
        )
        
        # Топ компаний по количеству вакансий
        top_companies = Company.objects.annotate(
            job_count=Count('jobs', filter=Q(jobs__is_active=True))
        ).filter(job_count__gt=0).order_by('-job_count')[:10]
        
        # Статистика по источникам
        source_stats = Job.objects.filter(is_active=True).values('source_site').annotate(
            count=Count('id')
        )
        
        analytics_data = {
            'total_jobs': total_jobs,
            'remote_jobs': remote_jobs,
            'remote_percentage': round((remote_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2),
            'companies_count': companies_count,
            'salary_stats': salary_stats,
            'experience_stats': list(experience_stats),
            'top_companies': [{'name': c.name, 'job_count': c.job_count} for c in top_companies],
            'source_stats': list(source_stats),
            'generated_at': timezone.now().isoformat()
        }
        
        # Кешируем результаты на 1 час
        cache.set('job_analytics', analytics_data, 3600)
        
        logger.info(f"Analytics generated: {total_jobs} jobs analyzed")
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error in analytics generation: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def update_application_reminders():
    """
    Send reminders for job applications that need follow-up
    """
    try:
        from .models import Application
        from .services import NotificationService
        
        logger.info("Starting application reminders task")
        
        # Получаем заявки с напоминаниями на сегодня
        today = timezone.now().date()
        applications_with_reminders = Application.objects.filter(
            reminder_date=today,
            user__profile__is_notifications_enabled=True,
            user__profile__telegram_chat_id__isnull=False
        ).exclude(user__profile__telegram_chat_id='')
        
        notification_service = NotificationService()
        sent_count = 0
        
        for application in applications_with_reminders:
            try:
                success = notification_service.send_application_reminder(
                    application.user.profile.telegram_chat_id,
                    application
                )
                
                if success:
                    sent_count += 1
                    # Очищаем дату напоминания после отправки
                    application.reminder_date = None
                    application.save()
                    
            except Exception as e:
                logger.error(f"Error sending reminder for application {application.id}: {str(e)}")
                continue
        
        logger.info(f"Application reminders completed: {sent_count} reminders sent")
        return f"Sent {sent_count} application reminders"
        
    except Exception as e:
        logger.error(f"Error in application reminders task: {str(e)}")
        return f"Error: {str(e)}" 