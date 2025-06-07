import json
import sqlite3
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

def create_database():
    """Create SQLite database with necessary tables"""
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        title TEXT,
        company TEXT,
        location INTEGER,
        salary_from REAL,
        salary_to REAL,
        remote_work BOOLEAN,
        publish_date TIMESTAMP,
        expiration_date TIMESTAMP,
        description TEXT,
        employer_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create companies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        employer_id INTEGER PRIMARY KEY,
        name TEXT,
        job_count INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn

def process_job_data(job: Dict[str, Any]) -> Dict[str, Any]:
    """Process and clean individual job data"""
    return {
        'id': job['id'],
        'title': job['title'],
        'company': job['company'],
        'location': job['location'],
        'salary_from': job['salaryFrom'],
        'salary_to': job['salaryTo'],
        'remote_work': job['remoteWork'],
        'publish_date': job['publishDate'],
        'expiration_date': job['expirationDate'],
        'description': job['description'] if job['description'] != 'null' else None,
        'employer_id': job['employerId']
    }

def store_jobs(conn: sqlite3.Connection, jobs: List[Dict[str, Any]]):
    """Store jobs in the database"""
    cursor = conn.cursor()
    
    for job in jobs:
        processed_job = process_job_data(job)
        
        # Insert or update job
        cursor.execute('''
        INSERT OR REPLACE INTO jobs (
            id, title, company, location, salary_from, salary_to,
            remote_work, publish_date, expiration_date, description, employer_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            processed_job['id'],
            processed_job['title'],
            processed_job['company'],
            processed_job['location'],
            processed_job['salary_from'],
            processed_job['salary_to'],
            processed_job['remote_work'],
            processed_job['publish_date'],
            processed_job['expiration_date'],
            processed_job['description'],
            processed_job['employer_id']
        ))
        
        # Update company statistics
        cursor.execute('''
        INSERT OR REPLACE INTO companies (employer_id, name, job_count, last_updated)
        VALUES (
            ?,
            ?,
            (SELECT COUNT(*) FROM jobs WHERE employer_id = ?),
            CURRENT_TIMESTAMP
        )
        ''', (processed_job['employer_id'], processed_job['company'], processed_job['employer_id']))
    
    conn.commit()

def analyze_jobs(conn: sqlite3.Connection):
    """Perform basic analysis on the job data"""
    # Convert to pandas DataFrame for analysis
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    
    print("\nJob Market Analysis:")
    print("-" * 50)
    
    # Total number of jobs
    print(f"Total number of jobs: {len(jobs_df)}")
    
    # Remote work statistics
    remote_jobs = jobs_df['remote_work'].sum()
    print(f"Remote jobs: {remote_jobs} ({remote_jobs/len(jobs_df)*100:.1f}%)")
    
    # Salary statistics
    jobs_with_salary = jobs_df[jobs_df['salary_from'].notna()]
    if not jobs_with_salary.empty:
        avg_salary = jobs_with_salary['salary_from'].mean()
        print(f"Average starting salary: {avg_salary:.2f}")
    
    # Top companies by number of jobs
    print("\nTop 5 companies by number of jobs:")
    company_stats = pd.read_sql_query("""
        SELECT name, job_count 
        FROM companies 
        ORDER BY job_count DESC 
        LIMIT 5
    """, conn)
    print(company_stats)

def main():
    # Create database connection
    conn = create_database()
    
    try:
        # Read job data
        with open('cv_ee_jobs.json', 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        # Store jobs in database
        store_jobs(conn, jobs)
        
        # Perform analysis
        analyze_jobs(conn)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 