from typing import List, Dict
from .models import Vacancy, JobScore
import re
import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import Job, UserProfile, Application

logger = logging.getLogger(__name__)

class JobScoringService:
    """Сервис для расчета релевантности вакансий"""
    
    # Ключевые слова для разных технологий
    TECH_KEYWORDS = {
        'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
        'javascript': ['javascript', 'js', 'node.js', 'react', 'vue', 'angular', 'typescript'],
        'java': ['java', 'spring', 'hibernate', 'maven', 'gradle'],
        'php': ['php', 'laravel', 'symfony', 'wordpress', 'drupal'],
        'csharp': ['c#', '.net', 'asp.net', 'entity framework'],
        'devops': ['docker', 'kubernetes', 'aws', 'azure', 'terraform', 'jenkins'],
        'data': ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch']
    }
    
    # Ключевые слова для уровней опыта
    EXPERIENCE_KEYWORDS = {
        'junior': ['junior', 'trainee', 'intern', 'entry', 'начинающий'],
        'middle': ['middle', 'mid', 'intermediate', 'средний'],
        'senior': ['senior', 'lead', 'principal', 'architect', 'старший']
    }

    def calculate_relevance_score(self, job: Job) -> int:
        """Расчет общего скора релевантности (0-100)"""
        try:
            score = 0
            text = f"{job.title} {job.description}".lower()
            
            # Базовый скор за наличие ключевых слов
            tech_score = self._calculate_tech_score(text)
            score += tech_score * 0.4
            
            # Скор за соответствие уровню опыта
            experience_score = self._calculate_experience_score(text, job.experience_level)
            score += experience_score * 0.2
            
            # Скор за актуальность (новые вакансии получают больше баллов)
            freshness_score = self._calculate_freshness_score(job.created_at)
            score += freshness_score * 0.2
            
            # Скор за полноту информации
            completeness_score = self._calculate_completeness_score(job)
            score += completeness_score * 0.2
            
            return min(100, max(0, int(score)))
            
        except Exception as e:
            logger.error(f"Error calculating relevance score for job {job.id}: {str(e)}")
            return 50  # Средний скор по умолчанию

    def calculate_skill_match_score(self, job: Job) -> int:
        """Расчет скора соответствия навыков (0-100)"""
        try:
            text = f"{job.title} {job.description} {job.requirements}".lower()
            
            # Подсчитываем количество найденных технологий
            found_techs = 0
            total_weight = 0
            
            for tech_category, keywords in self.TECH_KEYWORDS.items():
                category_weight = len(keywords)
                found_in_category = sum(1 for keyword in keywords if keyword in text)
                
                if found_in_category > 0:
                    found_techs += found_in_category
                    total_weight += category_weight
            
            if total_weight == 0:
                return 30  # Базовый скор если технологии не найдены
            
            # Нормализуем скор
            score = (found_techs / total_weight) * 100
            return min(100, max(0, int(score)))
            
        except Exception as e:
            logger.error(f"Error calculating skill match score for job {job.id}: {str(e)}")
            return 30

    def calculate_salary_score(self, job: Job) -> int:
        """Расчет скора по зарплате (0-100)"""
        try:
            if not job.salary_min:
                return 50  # Средний скор если зарплата не указана
            
            # Базовые пороги для IT в Эстонии (EUR/месяц)
            salary_ranges = {
                'junior': (1500, 3000),
                'middle': (3000, 5000),
                'senior': (5000, 8000)
            }
            
            min_expected, max_expected = salary_ranges.get(job.experience_level, (2000, 4000))
            
            if job.salary_min >= max_expected:
                return 100
            elif job.salary_min >= min_expected:
                # Линейная интерполяция между min и max
                ratio = (job.salary_min - min_expected) / (max_expected - min_expected)
                return int(50 + ratio * 50)
            else:
                # Ниже ожидаемого минимума
                ratio = job.salary_min / min_expected
                return int(ratio * 50)
                
        except Exception as e:
            logger.error(f"Error calculating salary score for job {job.id}: {str(e)}")
            return 50

    def calculate_location_score(self, job: Job) -> int:
        """Расчет скора по локации (0-100)"""
        try:
            location = job.location.lower()
            
            # Приоритет локаций для IT
            location_scores = {
                'tallinn': 100,
                'tartu': 90,
                'estonia': 85,
                'remote': 95,
                'hybrid': 90
            }
            
            # Проверяем удаленную работу
            if job.is_remote:
                return 95
            
            # Ищем совпадения в названии локации
            for loc, score in location_scores.items():
                if loc in location:
                    return score
            
            # Если локация не распознана, возвращаем средний скор
            return 60
            
        except Exception as e:
            logger.error(f"Error calculating location score for job {job.id}: {str(e)}")
            return 60

    def _calculate_tech_score(self, text: str) -> int:
        """Расчет скора по технологиям"""
        found_keywords = 0
        total_keywords = sum(len(keywords) for keywords in self.TECH_KEYWORDS.values())
        
        for keywords in self.TECH_KEYWORDS.values():
            found_keywords += sum(1 for keyword in keywords if keyword in text)
        
        return min(100, (found_keywords / total_keywords) * 100)

    def _calculate_experience_score(self, text: str, job_level: str) -> int:
        """Расчет скора по уровню опыта"""
        # Если уровень опыта в вакансии соответствует найденным ключевым словам
        if job_level in self.EXPERIENCE_KEYWORDS:
            keywords = self.EXPERIENCE_KEYWORDS[job_level]
            if any(keyword in text for keyword in keywords):
                return 100
        
        return 70  # Базовый скор если уровень не определен четко

    def _calculate_freshness_score(self, created_at) -> int:
        """Расчет скора по свежести вакансии"""
        if not created_at:
            return 50
        
        days_old = (timezone.now() - created_at).days
        
        if days_old <= 1:
            return 100
        elif days_old <= 7:
            return 90
        elif days_old <= 14:
            return 70
        elif days_old <= 30:
            return 50
        else:
            return 30

    def _calculate_completeness_score(self, job: Job) -> int:
        """Расчет скора по полноте информации"""
        score = 0
        
        # Проверяем наличие различных полей
        if job.title and len(job.title) > 10:
            score += 20
        if job.description and len(job.description) > 100:
            score += 30
        if job.requirements and len(job.requirements) > 50:
            score += 20
        if job.salary_min:
            score += 15
        if job.company_name:
            score += 15
        
        return min(100, score) 

class NotificationService:
    """Сервис для отправки уведомлений"""
    
    def __init__(self):
        self.telegram_bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.telegram_api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}"

    def send_telegram_notification(self, chat_id: str, jobs: List[Job]) -> bool:
        """Отправка уведомления о новых вакансиях в Telegram"""
        try:
            if not self.telegram_bot_token:
                logger.warning("Telegram bot token not configured")
                return False
            
            if not jobs:
                return True
            
            # Формируем сообщение
            message = "🔥 *Новые релевантные вакансии:*\n\n"
            
            for job in jobs[:5]:  # Ограничиваем до 5 вакансий
                score = getattr(job, 'jobscore', None)
                score_text = f" ({score.relevance_score}%)" if score else ""
                
                salary_text = ""
                if job.salary_min:
                    salary_text = f"\n💰 {job.salary_min}"
                    if job.salary_max:
                        salary_text += f"-{job.salary_max}"
                    salary_text += f" {job.salary_currency}"
                
                remote_text = " 🏠 Remote" if job.is_remote else ""
                
                message += f"*{job.title}*{score_text}\n"
                message += f"🏢 {job.company_name}\n"
                message += f"📍 {job.location}{remote_text}{salary_text}\n"
                message += f"🔗 [Подробнее]({job.source_url})\n\n"
            
            if len(jobs) > 5:
                message += f"И еще {len(jobs) - 5} вакансий...\n"
            
            message += "\n💡 Настройте фильтры в профиле для более точных уведомлений"
            
            # Отправляем сообщение
            response = requests.post(
                f"{self.telegram_api_url}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
            return False

    def send_application_reminder(self, chat_id: str, application: Application) -> bool:
        """Отправка напоминания о заявке"""
        try:
            if not self.telegram_bot_token:
                return False
            
            message = f"⏰ *Напоминание о заявке*\n\n"
            message += f"*{application.job.title}*\n"
            message += f"🏢 {application.job.company_name}\n"
            message += f"📅 Статус: {application.get_status_display()}\n"
            
            if application.notes:
                message += f"📝 Заметки: {application.notes[:100]}...\n"
            
            message += f"\n🔗 [Открыть вакансию]({application.job.source_url})"
            
            response = requests.post(
                f"{self.telegram_api_url}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                },
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending application reminder: {str(e)}")
            return False

    def filter_jobs_for_user(self, jobs: List[Job], user_profile: UserProfile) -> List[Job]:
        """Фильтрация вакансий по предпочтениям пользователя"""
        try:
            filtered_jobs = []
            
            # Получаем навыки пользователя
            user_skills = [skill.strip().lower() for skill in user_profile.skills.split(',') if skill.strip()]
            
            for job in jobs:
                # Проверяем минимальную зарплату
                if user_profile.min_salary and job.salary_min:
                    if job.salary_min < user_profile.min_salary:
                        continue
                
                # Проверяем локацию
                if user_profile.location_preference:
                    if (user_profile.location_preference.lower() not in job.location.lower() 
                        and not job.is_remote):
                        continue
                
                # Проверяем соответствие навыков
                if user_skills:
                    job_text = f"{job.title} {job.description} {job.requirements}".lower()
                    skill_match = any(skill in job_text for skill in user_skills)
                    if not skill_match:
                        continue
                
                filtered_jobs.append(job)
            
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"Error filtering jobs for user {user_profile.user.username}: {str(e)}")
            return jobs  # Возвращаем все вакансии в случае ошибки

class JobAnalyticsService:
    """Сервис для аналитики вакансий"""
    
    def get_market_trends(self) -> Dict:
        """Получение трендов рынка труда"""
        try:
            from .models import Job, Company
            from django.db.models import Count, Avg, Q
            from datetime import timedelta
            
            # Период для анализа трендов
            last_month = timezone.now() - timedelta(days=30)
            last_week = timezone.now() - timedelta(days=7)
            
            # Рост количества вакансий
            total_jobs = Job.objects.filter(is_active=True).count()
            jobs_last_month = Job.objects.filter(
                is_active=True, 
                created_at__gte=last_month
            ).count()
            jobs_last_week = Job.objects.filter(
                is_active=True, 
                created_at__gte=last_week
            ).count()
            
            # Топ технологий
            tech_keywords = ['python', 'javascript', 'java', 'react', 'node.js', 'django']
            tech_stats = {}
            
            for tech in tech_keywords:
                count = Job.objects.filter(
                    is_active=True,
                    description__icontains=tech
                ).count()
                tech_stats[tech] = count
            
            # Средние зарплаты по уровням
            salary_by_level = {}
            for level in ['junior', 'middle', 'senior']:
                avg_salary = Job.objects.filter(
                    is_active=True,
                    experience_level=level,
                    salary_min__isnull=False
                ).aggregate(avg=Avg('salary_min'))['avg']
                
                salary_by_level[level] = round(avg_salary) if avg_salary else None
            
            return {
                'total_jobs': total_jobs,
                'jobs_growth': {
                    'last_month': jobs_last_month,
                    'last_week': jobs_last_week
                },
                'top_technologies': dict(sorted(tech_stats.items(), key=lambda x: x[1], reverse=True)),
                'average_salaries': salary_by_level,
                'remote_percentage': self._calculate_remote_percentage()
            }
            
        except Exception as e:
            logger.error(f"Error getting market trends: {str(e)}")
            return {}

    def _calculate_remote_percentage(self) -> float:
        """Расчет процента удаленных вакансий"""
        try:
            from .models import Job
            
            total = Job.objects.filter(is_active=True).count()
            remote = Job.objects.filter(is_active=True, is_remote=True).count()
            
            return round((remote / total * 100) if total > 0 else 0, 2)
            
        except Exception as e:
            logger.error(f"Error calculating remote percentage: {str(e)}")
            return 0.0 