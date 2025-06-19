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
import xlsxwriter
from datetime import datetime
from django.views.generic import ListView, DetailView
import redis
import traceback
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Vacancy, ParsedJob, ParsedCompany, Job, Company, 
    JobScore, UserProfile, Application, Scraper
)
from .forms import FindForm, ParsedJobFilterForm
from .scrapers.linkedin_scraper import LinkedInScraper
from .services import JobAnalyticsService, NotificationService
from .tasks import scrape_all_sources, calculate_job_scores
from .scrapers.cv_ee_scraper import CVeeScraper
from .scrapers.cv_ee_selenium_scraper import CVeeSeleniumScraper


# Create your views here.
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
    """List all jobs with filtering and sorting options"""
    jobs = Job.objects.filter(is_active=True).select_related('company')
    
    # Filtering
    search = request.GET.get('search')
    source = request.GET.get('source')
    
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    if source:
        jobs = jobs.filter(source_site=source)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    jobs = jobs.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique sources for filter
    sources = Job.objects.values_list('source_site', flat=True).distinct()
    
    context = {
        'jobs': page_obj,
        'sources': sources,
        'current_filters': {
            'search': search,
            'source': source,
            'sort': sort_by
        }
    }
    return render(request, 'scraping/job_list.html', context)


def job_detail_view(request, job_id):
    """Detailed view of a specific job"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Get similar jobs
    similar_jobs = Job.objects.filter(
        is_active=True,
        job_type=job.job_type
    ).exclude(id=job.id).select_related('company')[:5]
    
    context = {
        'job': job,
        'similar_jobs': similar_jobs
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


@login_required
def update_application_status_view(request, application_id):
    """Обновление статуса заявки"""
    application = get_object_or_404(Application, id=application_id, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', application.notes)
        reminder_date = request.POST.get('reminder_date')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.notes = notes
            
            if reminder_date:
                try:
                    from datetime import datetime
                    application.reminder_date = datetime.strptime(reminder_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            application.save()
            messages.success(request, 'Статус заявки обновлен')
        
        return redirect('my_applications')
    
    context = {
        'application': application,
        'status_choices': Application.STATUS_CHOICES
    }
    return render(request, 'scraping/update_application.html', context)


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


class JobListView(ListView):
    model = Job
    template_name = 'scraping/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True).select_related('company')
        
        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(company_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Source filter
        source = self.request.GET.get('source', '')
        if source:
            queryset = queryset.filter(source_site=source)
        
        # Sort
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'salary':
            queryset = queryset.order_by('-salary_min')
        elif sort == 'date':
            queryset = queryset.order_by('-posted_date')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['source'] = self.request.GET.get('source', '')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        context['sources'] = Job.objects.values_list('source_site', flat=True).distinct()
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = 'scraping/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.select_related('company')


class ScraperManagementView(LoginRequiredMixin, ListView):
    model = Scraper
    template_name = 'scraping/scraper_management.html'
    context_object_name = 'scrapers'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        scraper_id = request.POST.get('scraper_id')

        if action == "run_all":
            scrapers = Scraper.objects.all()
            total = 0
            for scraper in scrapers:
                if scraper.source == 'cv_ee':
                    cv_scraper = CVeeSeleniumScraper()
                    jobs_created = cv_scraper.scrape_jobs()
                    total += jobs_created
                    scraper.status = 'completed'
                    scraper.last_run = timezone.now()
                    scraper.save()
                elif scraper.source == 'linkedin':
                    linkedin_scraper = LinkedInScraper()
                    jobs = linkedin_scraper.search_jobs(['python', 'django', 'flask'], 'Estonia', 5)
                    jobs_created = self._save_linkedin_jobs(jobs)
                    total += jobs_created
                    scraper.status = 'completed'
                    scraper.last_run = timezone.now()
                    scraper.save()
                    # Здесь будет cvkeskus.ee
            messages.success(request, f'All scrapers finished. Total jobs scraped: {total}')
            return redirect('scraping:scraper_management')

        if not scraper_id or not action:
            messages.error(request, 'Invalid request')
            return redirect('scraping:scraper_management')

        try:
            scraper = Scraper.objects.get(id=scraper_id)
            if action == 'start':
                if scraper.source == 'cv_ee':
                    scraper.status = 'running'
                    scraper.save()
                    cv_scraper = CVeeSeleniumScraper()
                    jobs_created = cv_scraper.scrape_jobs()
                    scraper.status = 'completed'
                    scraper.last_run = timezone.now()
                    scraper.save()
                    messages.success(request, f'Successfully scraped {jobs_created} jobs from cv.ee')
                elif scraper.source == 'linkedin':
                    scraper.status = 'running'
                    scraper.save()
                    linkedin_scraper = LinkedInScraper()
                    jobs = linkedin_scraper.search_jobs(['python', 'django', 'flask'], 'Estonia', 5)
                    jobs_created = self._save_linkedin_jobs(jobs)
                    scraper.status = 'completed'
                    scraper.last_run = timezone.now()
                    scraper.save()
                    messages.success(request, f'Successfully scraped {jobs_created} jobs from LinkedIn')
                    # Здесь будет cvkeskus.ee
                else:
                    messages.error(request, f'Scraper for {scraper.source} is not implemented yet')
            elif action == 'stop':
                scraper.status = 'idle'
                scraper.save()
                messages.info(request, f'Stopping scraper for {scraper.source}')
            else:
                messages.error(request, 'Invalid action')
        except Scraper.DoesNotExist:
            messages.error(request, 'Scraper not found')
        return redirect('scraping:scraper_management')

    def _save_linkedin_jobs(self, jobs):
        """Сохранить вакансии LinkedIn в базу данных"""
        jobs_created = 0
        for job_data in jobs:
            try:
                job, created = Job.objects.get_or_create(
                    source_url=job_data.get('url', ''),
                    defaults={
                        'title': job_data.get('title', ''),
                        'company_name': job_data.get('company', ''),
                        'location': job_data.get('location', ''),
                        'description': job_data.get('description', ''),
                        'source_site': 'linkedin',
                        'salary_min': job_data.get('salary_min'),
                        'salary_max': job_data.get('salary_max'),
                        'is_active': True
                    }
                )
                if created:
                    jobs_created += 1
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving LinkedIn job: {str(e)}")
        return jobs_created


@login_required
def export_jobs_csv(request):
    """Export jobs to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Company', 'Location', 'Description', 
        'Requirements', 'Salary', 'Job Type', 'Experience Level',
        'Education', 'Employment Type', 'Remote', 'Source',
        'Created At', 'Status'
    ])
    
    jobs = Job.objects.filter(is_active=True).select_related('company')
    
    for job in jobs:
        writer.writerow([
            job.title,
            job.company_name,
            job.location,
            job.description,
            job.requirements,
            job.salary,
            job.job_type,
            job.experience_level,
            job.education,
            job.employment_type,
            'Yes' if job.remote else 'No',
            job.source,
            job.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            job.status
        ])
    
    return response


@login_required
def export_jobs_excel(request):
    """Export jobs to Excel"""
    jobs = Job.objects.filter(is_active=True).select_related('company')
    
    data = []
    for job in jobs:
        data.append({
            'Title': job.title,
            'Company': job.company_name,
            'Location': job.location,
            'Description': job.description,
            'Requirements': job.requirements,
            'Salary': job.salary,
            'Job Type': job.job_type,
            'Experience Level': job.experience_level,
            'Education': job.education,
            'Employment Type': job.employment_type,
            'Remote': 'Yes' if job.remote else 'No',
            'Source': job.source,
            'Created At': job.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Status': job.status
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Jobs', index=False)
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="jobs.xlsx"'
    
    return response


def export_analytics_report(request):
    """Export comprehensive analytics report to Excel"""
    # Get analytics data
    total_jobs = ParsedJob.objects.count()
    remote_jobs = ParsedJob.objects.filter(remote_work=True).count()
    
    from django.db.models import Min, Max
    salary_stats = ParsedJob.objects.filter(
        salary_from__isnull=False
    ).aggregate(
        avg_salary=Avg('salary_from'),
        min_salary=Min('salary_from'),
        max_salary=Max('salary_from')
    )
    
    top_companies = ParsedCompany.objects.annotate(
        job_count=Count('parsedjob')
    ).order_by('-job_count')[:20]
    
    location_stats = ParsedJob.objects.values('location').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # Create Excel file with multiple sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Metric': ['Total Jobs', 'Remote Jobs', 'Remote Percentage', 'Average Salary', 'Min Salary', 'Max Salary'],
            'Value': [
                total_jobs,
                remote_jobs,
                f"{(remote_jobs / total_jobs * 100):.1f}%" if total_jobs > 0 else "0%",
                f"€{salary_stats['avg_salary']:.0f}" if salary_stats['avg_salary'] else "N/A",
                f"€{salary_stats['min_salary']:.0f}" if salary_stats['min_salary'] else "N/A",
                f"€{salary_stats['max_salary']:.0f}" if salary_stats['max_salary'] else "N/A"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Top companies sheet
        companies_data = [{'Company': c.name, 'Job Count': c.job_count} for c in top_companies]
        pd.DataFrame(companies_data).to_excel(writer, sheet_name='Top Companies', index=False)
        
        # Top locations sheet
        locations_data = [{'Location': l['location'], 'Job Count': l['count']} for l in location_stats]
        pd.DataFrame(locations_data).to_excel(writer, sheet_name='Top Locations', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="analytics_report.xlsx"'
    
    return response


def export_jobs(request):
    format_type = request.GET.get('format', 'csv')
    queryset = Job.objects.filter(is_active=True).select_related('company')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="jobs_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Company', 'Location', 'Salary', 'Posted Date', 'Source'])
        
        for job in queryset:
            salary = f"{job.salary_min}-{job.salary_max} {job.salary_currency}" if job.salary_min and job.salary_max else "Not specified"
            writer.writerow([
                job.title,
                job.company_name,
                job.location,
                salary,
                job.posted_date.strftime('%Y-%m-%d'),
                job.source_site
            ])
        
        return response
    
    elif format_type == 'excel':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Add headers
        headers = ['Title', 'Company', 'Location', 'Salary', 'Posted Date', 'Source']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Add data
        for row, job in enumerate(queryset, start=1):
            salary = f"{job.salary_min}-{job.salary_max} {job.salary_currency}" if job.salary_min and job.salary_max else "Not specified"
            worksheet.write(row, 0, job.title)
            worksheet.write(row, 1, job.company_name)
            worksheet.write(row, 2, job.location)
            worksheet.write(row, 3, salary)
            worksheet.write(row, 4, job.posted_date.strftime('%Y-%m-%d'))
            worksheet.write(row, 5, job.source_site)
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="jobs_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        
        return response
    
    return HttpResponse('Invalid format', status=400)


def scraper_progress_api(request, scraper_name):
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1, socket_timeout=1)
        # Проверяем подключение
        r.ping()
        progress = r.get(f'scraper_progress:{scraper_name}')
        total_jobs = r.get(f'scraper_total_jobs:{scraper_name}')
        collected_jobs = r.get(f'scraper_collected_jobs:{scraper_name}')
        
        return JsonResponse({
            'progress': int(progress) if progress else 0,
            'total_jobs': int(total_jobs) if total_jobs else 0,
            'collected_jobs': int(collected_jobs) if collected_jobs else 0
        })
    except redis.ConnectionError:
        # Redis не запущен или недоступен
        return JsonResponse({
            'progress': 0, 
            'total_jobs': 0,
            'collected_jobs': 0,
            'error': 'Redis server not available'
        })
    except Exception as e:
        # Другие ошибки
        return JsonResponse({
            'progress': 0, 
            'total_jobs': 0,
            'collected_jobs': 0,
            'error': f'Redis error: {str(e)}'
        })


@csrf_exempt
def test_scraper(request, scraper_id):
    """Test scraper and return first job"""
    if request.method == 'GET':
        try:
            scraper = Scraper.objects.get(id=scraper_id)
            result = scraper.test_scraper()
            
            if isinstance(result, dict) and 'error' in result:
                return JsonResponse({'success': False, 'error': result['error']})
            
            if result:
                # Если результат - список, берем первый элемент
                job_data = result[0] if isinstance(result, list) else result
                return JsonResponse({
                    'success': True,
                    'job': {
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company', ''),
                        'location': job_data.get('location', ''),
                        'description': job_data.get('description', '')[:200] + '...' if job_data.get('description') else '',
                        'url': job_data.get('url', '')
                    }
                })
            else:
                return JsonResponse({'success': False, 'error': 'No jobs found'})
        except Scraper.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Scraper not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def get_latest_jobs(request, scraper_id):
    """Get latest jobs from scraper"""
    if request.method == 'GET':
        try:
            scraper = Scraper.objects.get(id=scraper_id)
            result = scraper.get_latest_jobs(limit=10)
            
            if isinstance(result, dict) and 'error' in result:
                return JsonResponse({'success': False, 'error': result['error']})
            
            if result:
                jobs_data = []
                for job in result:
                    jobs_data.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', ''),
                        'description': job.get('description', '')[:150] + '...' if job.get('description') else '',
                        'url': job.get('url', ''),
                        'salary_min': job.get('salary_min'),
                        'salary_max': job.get('salary_max')
                    })
                
                return JsonResponse({
                    'success': True,
                    'jobs': jobs_data,
                    'count': len(jobs_data)
                })
            else:
                return JsonResponse({'success': False, 'error': 'No jobs found'})
        except Scraper.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Scraper not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})