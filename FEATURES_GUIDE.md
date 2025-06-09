# Job Scraping Platform - Features Guide

This guide covers all the advanced features implemented in the job scraping platform.

## 🔍 1. Advanced Filtering & Search

### Features:
- **Search**: Search jobs by title, description, or company name
- **Company Filter**: Filter by specific company names
- **Location Filter**: Filter by job location
- **Salary Range**: Filter by minimum and maximum salary
- **Remote Work**: Filter for remote vs on-site positions

### Usage:
1. Navigate to `/parsed-jobs/`
2. Use the filter form at the top of the page
3. Apply multiple filters simultaneously
4. Use the "Clear" button to reset all filters

## 📄 2. Pagination

### Features:
- 20 jobs per page (configurable)
- Navigation with First, Previous, Next, Last buttons
- Page numbers with smart truncation
- Maintains filter parameters across pages

### Usage:
- Pagination automatically appears when there are more than 20 jobs
- Click page numbers or navigation buttons to browse
- Filters are preserved when navigating between pages

## 🤖 3. Automated Scraping with Celery

### Setup:
1. **Install Redis** (required for Celery broker):
   ```bash
   # Windows (using Chocolatey)
   choco install redis-64
   
   # Or download from: https://github.com/microsoftarchive/redis/releases
   ```

2. **Start Redis server**:
   ```bash
   redis-server
   ```

3. **Start Celery Worker**:
   ```bash
   celery -A config worker --loglevel=info
   ```

4. **Start Celery Beat** (for scheduled tasks):
   ```bash
   celery -A config beat --loglevel=info
   ```

5. **Setup Periodic Tasks**:
   ```bash
   python manage.py setup_periodic_tasks
   ```

### Available Tasks:
- **Daily CV Keskus Scraping**: Scrapes CV Keskus daily
- **Weekly Comprehensive Scraping**: Scrapes all sources weekly
- **Daily Cleanup**: Removes expired job postings
- **Daily Analytics**: Generates job market statistics

### Manual Task Execution:
```python
# In Django shell
from apps.scraping.tasks import scrape_cv_keskus, generate_job_analytics

# Run immediately
result = scrape_cv_keskus.delay()
analytics = generate_job_analytics.delay()
```

## 📊 4. Analytics Dashboard

### Features:
- **Key Metrics**: Total jobs, remote jobs percentage, average salary
- **Interactive Charts**: Jobs over time, salary distribution
- **Top Companies**: Companies with most job postings
- **Location Statistics**: Most popular job locations
- **Salary Analysis**: Min, max, and average salaries

### Usage:
1. Navigate to `/analytics/`
2. View real-time job market insights
3. Charts are interactive and update automatically
4. Export analytics reports to Excel

### Charts:
- **Line Chart**: Jobs posted over the last 30 days
- **Doughnut Chart**: Salary range distribution

## 📤 5. Export Functionality

### Available Exports:

#### CSV Export (`/export/csv/`)
- Exports filtered job listings to CSV format
- Includes all job details
- Respects current filter settings
- Compatible with Excel and Google Sheets

#### Excel Export (`/export/excel/`)
- Exports filtered job listings to Excel format
- Professional formatting
- Includes all job details
- Respects current filter settings

#### Analytics Report (`/export/analytics/`)
- Comprehensive Excel report with multiple sheets:
  - **Summary**: Key metrics and statistics
  - **Top Companies**: Companies ranked by job count
  - **Top Locations**: Locations ranked by job count

### Usage:
1. **From Job Listings**: Use export buttons on `/parsed-jobs/`
2. **From Analytics**: Use export button on `/analytics/`
3. **Direct URLs**: Access export URLs directly with filters

## 🛠️ Technical Implementation

### Database Models:
- **ParsedJob**: Stores individual job postings
- **ParsedCompany**: Stores company information
- **Celery Tables**: Task results and scheduling

### Key Technologies:
- **Django**: Web framework
- **Celery**: Background task processing
- **Redis**: Message broker and result backend
- **Pandas**: Data processing for exports
- **Chart.js**: Interactive charts
- **Bootstrap**: Responsive UI
- **Selenium**: Web scraping

### File Structure:
```
apps/scraping/
├── tasks.py                 # Celery tasks
├── forms.py                 # Filter forms
├── views.py                 # Views with filtering/export
├── management/commands/
│   ├── import_parsed_jobs.py
│   └── setup_periodic_tasks.py
└── templates/scraping/
    ├── parsed_jobs_list.html
    └── analytics_dashboard.html
```

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Import Existing Data**:
   ```bash
   python manage.py import_parsed_jobs
   ```

4. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

5. **Setup Celery** (optional, for background tasks):
   - Install and start Redis
   - Start Celery worker and beat
   - Setup periodic tasks

## 📱 Usage Examples

### Filtering Jobs:
- Search for "Python developer" jobs
- Filter by salary range €2000-€4000
- Show only remote positions
- Export results to Excel

### Analytics:
- View job market trends
- Identify top hiring companies
- Analyze salary distributions
- Export comprehensive reports

### Automation:
- Schedule daily scraping
- Automatic data cleanup
- Regular analytics updates
- Background processing

## 🔧 Configuration

### Celery Settings (config/settings.py):
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### Pagination Settings:
```python
# In views.py
paginator = Paginator(jobs, 20)  # 20 jobs per page
```

## 🐛 Troubleshooting

### Common Issues:

1. **Redis Connection Error**:
   - Ensure Redis server is running
   - Check Redis connection settings

2. **Celery Tasks Not Running**:
   - Start Celery worker
   - Check task registration
   - Verify Redis connectivity

3. **Export Errors**:
   - Ensure openpyxl is installed
   - Check file permissions
   - Verify data integrity

4. **Chart Not Loading**:
   - Check Chart.js CDN
   - Verify JSON data format
   - Check browser console for errors

## 📈 Performance Tips

1. **Database Optimization**:
   - Use select_related() for foreign keys
   - Add database indexes for frequently filtered fields
   - Regular database maintenance

2. **Caching**:
   - Cache analytics results
   - Use Redis for session storage
   - Implement query result caching

3. **Background Processing**:
   - Use Celery for heavy operations
   - Schedule tasks during off-peak hours
   - Monitor task performance

## 🔮 Future Enhancements

- **Email Notifications**: Job alerts and reports
- **API Endpoints**: RESTful API for external access
- **Advanced Analytics**: Machine learning insights
- **Multi-language Support**: Internationalization
- **Real-time Updates**: WebSocket notifications
- **Mobile App**: React Native companion app 