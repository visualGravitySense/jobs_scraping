# Job Scraping Platform

A Django-based platform for scraping and managing job listings from various sources.

## Features

- Multi-source job scraping (cv.ee, LinkedIn, etc.)
- Job listing management and filtering
- Export functionality (CSV, Excel)
- Scraper management interface
- Real-time job status updates
- Email notifications
- Telegram bot integration

## Requirements

- Python 3.8+
- Django 3.2+
- Redis
- Celery
- PostgreSQL (recommended) or SQLite
- Chrome/Chromium (for Selenium scrapers)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jobs_scraping.git
cd jobs_scraping
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start Redis server:
```bash
redis-server
```

8. Start Celery worker:
```bash
celery -A config worker -l info
```

9. Start Celery beat:
```bash
celery -A config beat -l info
```

10. Run the development server:
```bash
python manage.py runserver
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Scraper Configuration

Scraper settings can be configured in `config/settings.py`:

```python
SCRAPER_CONFIG = {
    'cv_ee': {
        'base_url': 'https://www.cv.ee',
        'search_url': 'https://www.cv.ee/toopakkumised',
        'max_pages': 10,
    },
    'linkedin': {
        'base_url': 'https://www.linkedin.com',
        'search_url': 'https://www.linkedin.com/jobs/search',
        'max_pages': 5,
    },
}
```

## Usage

### Running Scrapers

1. Access the scraper management interface at `/scrapers/`
2. Click "Run Now" to start a specific scraper
3. Use "Run All Scrapers" to start all configured scrapers

### Viewing Jobs

1. Access the job list at `/`
2. Use filters to find specific jobs
3. Click on a job to view details

### Exporting Data

1. Access the export options at `/export/csv/` or `/export/excel/`
2. Download the file in your preferred format

## Development

### Project Structure

```
jobs_scraping/
├── apps/
│   ├── accounts/
│   └── scraping/
│       ├── management/
│       ├── scrapers/
│       ├── templates/
│       └── tests/
├── config/
├── logs/
├── media/
├── static/
└── templates/
```

### Adding New Scrapers

1. Create a new scraper class in `apps/scraping/scrapers/`
2. Implement the required methods:
   - `__init__`
   - `run`
   - `parse_job`
3. Add the scraper to `SCRAPER_CONFIG` in settings
4. Register the scraper in `apps/scraping/tasks.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

