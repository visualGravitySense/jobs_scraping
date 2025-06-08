from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponse
import json
import csv
import pandas as pd
from io import BytesIO

from .models import Vacancy, ParsedJob, ParsedCompany
from .forms import FindForm, ParsedJobFilterForm
from .scrapers.linkedin_scraper import LinkedInScraper


# Create your views here.
def home_view(request):
    form = FindForm()
    return render(request, 'scraping/home.html', {'form': form})


def list_view(request):
    #print(request.GET)
    form = FindForm()
    city = request.GET.get('city')
    language = request.GET.get('language')
    context = {'city': city, 'language': language, 'form': form}
    if city or language:
        _filter = {}
        if city:
            _filter['city__slug'] = city
        if language:
            _filter['language__slug'] = language

        qs = Vacancy.objects.filter(**_filter)
        paginator = Paginator(qs, 10)

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['object_list'] = page_obj
    return render(request, 'scraping/list.html', context)


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
            return redirect('home')  # Replace with your home URL name
            
        try:
            auth = LinkedInScraper.handle_auth_callback(code)
            messages.success(request, "Successfully authenticated with LinkedIn")
        except Exception as e:
            messages.error(request, f"Error authenticating with LinkedIn: {str(e)}")
            
        return redirect('home')  # Replace with your home URL name


def parsed_jobs_list_view(request):
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


def analytics_dashboard_view(request):
    """Analytics dashboard with job market insights"""
    # Basic statistics
    total_jobs = ParsedJob.objects.count()
    remote_jobs = ParsedJob.objects.filter(remote_work=True).count()
    remote_percentage = (remote_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Salary statistics
    from django.db.models import Min, Max
    salary_stats = ParsedJob.objects.filter(
        salary_from__isnull=False
    ).aggregate(
        avg_salary=Avg('salary_from'),
        min_salary=Min('salary_from'),
        max_salary=Max('salary_from')
    )
    
    # Top companies by job count
    top_companies = ParsedCompany.objects.annotate(
        job_count=Count('parsedjob')
    ).order_by('-job_count')[:10]
    
    # Jobs by location
    location_stats = ParsedJob.objects.values('location').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Jobs posted over time (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    jobs_over_time = ParsedJob.objects.filter(
        publish_date__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(publish_date)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Salary ranges distribution
    salary_ranges = [
        {'range': '0-1000', 'count': ParsedJob.objects.filter(salary_from__lt=1000).count()},
        {'range': '1000-2000', 'count': ParsedJob.objects.filter(salary_from__gte=1000, salary_from__lt=2000).count()},
        {'range': '2000-3000', 'count': ParsedJob.objects.filter(salary_from__gte=2000, salary_from__lt=3000).count()},
        {'range': '3000-4000', 'count': ParsedJob.objects.filter(salary_from__gte=3000, salary_from__lt=4000).count()},
        {'range': '4000+', 'count': ParsedJob.objects.filter(salary_from__gte=4000).count()},
    ]
    
    context = {
        'total_jobs': total_jobs,
        'remote_jobs': remote_jobs,
        'remote_percentage': round(remote_percentage, 1),
        'salary_stats': salary_stats,
        'top_companies': top_companies,
        'location_stats': location_stats,
        'jobs_over_time': list(jobs_over_time),
        'jobs_over_time_json': json.dumps(list(jobs_over_time), default=str),
        'salary_ranges': salary_ranges,
        'salary_ranges_json': json.dumps(salary_ranges),
    }
    
    return render(request, 'scraping/analytics_dashboard.html', context)


def export_jobs_csv(request):
    """Export jobs to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Company', 'Location', 'Salary From', 'Salary To', 
        'Remote Work', 'Publish Date', 'Expiration Date', 'Description'
    ])
    
    # Apply same filters as the list view
    jobs = ParsedJob.objects.all().select_related('employer')
    form = ParsedJobFilterForm(request.GET)
    
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
    
    for job in jobs:
        writer.writerow([
            job.title,
            job.company,
            job.location,
            job.salary_from or '',
            job.salary_to or '',
            'Yes' if job.remote_work else 'No',
            job.publish_date.strftime('%Y-%m-%d') if job.publish_date else '',
            job.expiration_date.strftime('%Y-%m-%d') if job.expiration_date else '',
            job.description or ''
        ])
    
    return response


def export_jobs_excel(request):
    """Export jobs to Excel format"""
    # Apply same filters as the list view
    jobs = ParsedJob.objects.all().select_related('employer')
    form = ParsedJobFilterForm(request.GET)
    
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
    
    # Create DataFrame
    data = []
    for job in jobs:
        data.append({
            'Title': job.title,
            'Company': job.company,
            'Location': job.location,
            'Salary From': job.salary_from,
            'Salary To': job.salary_to,
            'Remote Work': 'Yes' if job.remote_work else 'No',
            'Publish Date': job.publish_date.strftime('%Y-%m-%d') if job.publish_date else '',
            'Expiration Date': job.expiration_date.strftime('%Y-%m-%d') if job.expiration_date else '',
            'Description': job.description or ''
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Jobs', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="jobs_export.xlsx"'
    
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