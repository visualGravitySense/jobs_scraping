from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json
import csv
import pandas as pd
from io import BytesIO

from .models import (
    Vacancy, ParsedJob, ParsedCompany, Job, Company, 
    JobScore, UserProfile, Application
)
from .forms import FindForm, ParsedJobFilterForm
from .scrapers.linkedin_scraper import LinkedInScraper
from .services import JobAnalyticsService, NotificationService
from .tasks import scrape_all_sources, calculate_job_scores


def home_view(request):
    """Главная страница с поиском вакансий"""
    form = FindForm()
    
    # Получаем статистику для главной страницы
    analytics_data = cache.get('job_analytics')
    if not analytics_data:
        analytics_service = JobAnalyticsService()
        analytics_data = analytics_service.get_market_trends()
        cache.set('job_analytics', analytics_data, 3600)  # Кешируем на час
    
    # Получаем последние вакансии
    recent_jobs = Job.objects.filter(is_active=True).select_related('company').order_by('-created_at')[:6]
    
    context = {
        'form': form,
        'analytics': analytics_data,
        'recent_jobs': recent_jobs
    }
    return render(request, 'scraping/home.html', context)


def job_list_view(request):
    """Список всех вакансий с фильтрацией"""
    jobs = Job.objects.filter(is_active=True).select_related('company', 'jobscore')
    
    # Фильтрация
    search = request.GET.get('search')
    location = request.GET.get('location')
    company = request.GET.get('company')
    min_salary = request.GET.get('min_salary')
    max_salary = request.GET.get('max_salary')
    is_remote = request.GET.get('is_remote')
    experience_level = request.GET.get('experience_level')
    source_site = request.GET.get('source_site')
    
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(requirements__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    if company:
        jobs = jobs.filter(company_name__icontains=company)
    
    if min_salary:
        try:
            jobs = jobs.filter(salary_min__gte=int(min_salary))
        except ValueError:
            pass
    
    if max_salary:
        try:
            jobs = jobs.filter(salary_max__lte=int(max_salary))
        except ValueError:
            pass
    
    if is_remote == 'true':
        jobs = jobs.filter(is_remote=True)
    elif is_remote == 'false':
        jobs = jobs.filter(is_remote=False)
    
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    if source_site:
        jobs = jobs.filter(source_site=source_site)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'relevance':
        jobs = jobs.order_by('-jobscore__relevance_score', '-created_at')
    elif sort_by == 'salary':
        jobs = jobs.order_by('-salary_min', '-created_at')
    elif sort_by == 'company':
        jobs = jobs.order_by('company_name', '-created_at')
    else:
        jobs = jobs.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем уникальные значения для фильтров
    locations = Job.objects.filter(is_active=True).values_list('location', flat=True).distinct()
    companies = Job.objects.filter(is_active=True).values_list('company_name', flat=True).distinct()
    
    context = {
        'object_list': page_obj,
        'total_jobs': jobs.count(),
        'page_obj': page_obj,
        'locations': [loc for loc in locations if loc],
        'companies': [comp for comp in companies if comp],
        'experience_levels': Job.EXPERIENCE_LEVELS,
        'source_sites': Job.SOURCE_SITES,
        'current_filters': {
            'search': search,
            'location': location,
            'company': company,
            'min_salary': min_salary,
            'max_salary': max_salary,
            'is_remote': is_remote,
            'experience_level': experience_level,
            'source_site': source_site,
            'sort': sort_by
        }
    }
    return render(request, 'scraping/job_list.html', context)


def job_detail_view(request, job_id):
    """Детальная страница вакансии"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Получаем скор вакансии
    try:
        job_score = job.jobscore
    except JobScore.DoesNotExist:
        job_score = None
    
    # Получаем похожие вакансии
    similar_jobs = Job.objects.filter(
        is_active=True,
        experience_level=job.experience_level
    ).exclude(id=job.id).select_related('company')[:5]
    
    # Проверяем, подавал ли пользователь заявку на эту вакансию
    user_application = None
    if request.user.is_authenticated:
        try:
            user_application = Application.objects.get(user=request.user, job=job)
        except Application.DoesNotExist:
            pass
    
    context = {
        'job': job,
        'job_score': job_score,
        'similar_jobs': similar_jobs,
        'user_application': user_application
    }
    return render(request, 'scraping/job_detail.html', context)


@login_required
def apply_to_job_view(request, job_id):
    """Подача заявки на вакансию"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Проверяем, не подавал ли пользователь уже заявку
    existing_application = Application.objects.filter(user=request.user, job=job).first()
    if existing_application:
        messages.warning(request, 'Вы уже подавали заявку на эту вакансию')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Создаем заявку
        application = Application.objects.create(
            user=request.user,
            job=job,
            status='applied',
            notes=notes,
            applied_at=timezone.now()
        )
        
        messages.success(request, 'Заявка успешно подана!')
        return redirect('job_detail', job_id=job.id)
    
    return render(request, 'scraping/apply_to_job.html', {'job': job})


@login_required
def my_applications_view(request):
    """Список заявок пользователя"""
    applications = Application.objects.filter(user=request.user).select_related('job').order_by('-applied_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Пагинация
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'page_obj': page_obj,
        'status_choices': Application.STATUS_CHOICES,
        'current_status': status_filter
    }
    return render(request, 'scraping/my_applications.html', context)


def analytics_dashboard_view(request):
    """Аналитическая панель с инсайтами рынка труда"""
    # Получаем данные из кеша или рассчитываем заново
    analytics_data = cache.get('job_analytics')
    if not analytics_data:
        analytics_service = JobAnalyticsService()
        analytics_data = analytics_service.get_market_trends()
        cache.set('job_analytics', analytics_data, 3600)
    
    # Дополнительная статистика для дашборда
    total_jobs = Job.objects.filter(is_active=True).count()
    total_companies = Company.objects.count()
    
    # Статистика по зарплатам
    salary_stats = Job.objects.filter(
        is_active=True,
        salary_min__isnull=False
    ).aggregate(
        avg_salary=Avg('salary_min'),
        min_salary=Avg('salary_min'),
        max_salary=Avg('salary_max')
    )
    
    # Топ компаний по количеству вакансий
    top_companies = Company.objects.annotate(
        job_count=Count('jobs', filter=Q(jobs__is_active=True))
    ).filter(job_count__gt=0).order_by('-job_count')[:10]
    
    # Статистика по локациям
    location_stats = Job.objects.filter(is_active=True).values('location').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Вакансии за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    jobs_over_time = Job.objects.filter(
        is_active=True,
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Распределение по уровням опыта
    experience_stats = Job.objects.filter(is_active=True).values('experience_level').annotate(
        count=Count('id')
    )
    
    context = {
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'analytics_data': analytics_data,
        'salary_stats': salary_stats,
        'top_companies': top_companies,
        'location_stats': location_stats,
        'jobs_over_time': list(jobs_over_time),
        'jobs_over_time_json': json.dumps(list(jobs_over_time), default=str),
        'experience_stats': list(experience_stats),
        'experience_stats_json': json.dumps(list(experience_stats))
    }
    
    return render(request, 'scraping/analytics_dashboard.html', context)


def trigger_scraping_view(request):
    """Запуск парсинга вакансий (только для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Запускаем парсинг асинхронно
            task = scrape_all_sources.delay()
            messages.success(request, f'Парсинг запущен. ID задачи: {task.id}')
        except Exception as e:
            messages.error(request, f'Ошибка при запуске парсинга: {str(e)}')
    
    return redirect('analytics_dashboard')


def export_jobs_csv(request):
    """Export jobs to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Company', 'Location', 'Salary Min', 'Salary Max', 
        'Remote Work', 'Experience Level', 'Source', 'Created Date', 'Description'
    ])
    
    # Экспортируем новые вакансии
    jobs = Job.objects.filter(is_active=True).select_related('company')
    
    for job in jobs:
        writer.writerow([
            job.title,
            job.company_name,
            job.location,
            job.salary_min or '',
            job.salary_max or '',
            'Yes' if job.is_remote else 'No',
            job.get_experience_level_display(),
            job.get_source_site_display(),
            job.created_at.strftime('%Y-%m-%d'),
            job.description[:500] + '...' if len(job.description) > 500 else job.description
        ])
    
    return response


# Старые views для обратной совместимости
def list_view(request):
    """Старый view для списка вакансий - редирект на новый"""
    return redirect('job_list')


class LinkedInAuthView(View):
    def get(self, request):
        """Redirect to LinkedIn authorization page"""
        auth_url = LinkedInScraper.get_auth_url()
        return redirect(auth_url)


class LinkedInCallbackView(View):
    def get(self, request):
        """Handle LinkedIn OAuth callback"""
        code = request.GET.get('code')
        if not code:
            messages.error(request, "No authorization code received from LinkedIn")
            return redirect('home')
            
        try:
            auth = LinkedInScraper.handle_auth_callback(code)
            messages.success(request, "Successfully authenticated with LinkedIn")
        except Exception as e:
            messages.error(request, f"Error authenticating with LinkedIn: {str(e)}")
            
        return redirect('home')


def parsed_jobs_list_view(request):
    """Старый view для парсированных вакансий"""
    jobs = ParsedJob.objects.all().select_related('employer')
    form = ParsedJobFilterForm(request.GET)
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        company = form.cleaned_data.get('company')
        location = form.cleaned_data.get('location')
        salary_from = form.cleaned_data.get('salary_from')
        salary_to = form.cleaned_data.get('salary_to')
        remote_work = form.cleaned_data.get('remote_work')
        
        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(company__icontains=search)
            )
        
        if company:
            jobs = jobs.filter(company__icontains=company)
            
        if location:
            jobs = jobs.filter(location__icontains=location)
            
        if salary_from:
            jobs = jobs.filter(salary_from__gte=salary_from)
            
        if salary_to:
            jobs = jobs.filter(salary_to__lte=salary_to)
            
        if remote_work:
            jobs = jobs.filter(remote_work=(remote_work == 'true'))
    
    # Order by publish date (newest first)
    jobs = jobs.order_by('-publish_date', '-id')
    
    # Pagination
    paginator = Paginator(jobs, 20)  # 20 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'object_list': page_obj,
        'form': form,
        'total_jobs': jobs.count(),
        'page_obj': page_obj,
    }
    return render(request, 'scraping/parsed_jobs_list.html', context) 