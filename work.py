import requests
import codecs
from bs4 import BeautifulSoup as BS
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

"""
# Temporarily disabled Ukrainian job sites
def work(url):
    jobs = []
    errors = []
    domain = 'https://www.work.ua'
    url = 'https://www.work.ua/ru/jobs-kyiv-python/'
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BS(resp.content, 'html.parser')
        main_div = soup.find('div', id='pjax-job-list')
        if main_div:
            div_list = main_div.find_all('div', attrs={'class': 'job-link'})
            for div in div_list:
                title = div.find('h2')
                href = title.a['href']
                content = div.p.text
                company = 'No name'
                logo = div.find('img')
                if logo:
                    company = logo['alt']
                jobs.append({'title': title.text, 'url': domain + href,
                             'description': content, 'company': company})
        else:
            errors.append({'url': url, 'title': "Div does not exists"})
    else:
        errors.append({'url': url, 'title': "Page not response"})

    return jobs, errors


def rabota(url):
    jobs = []
    errors = []
    domain = 'https://rabota.ua'
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BS(resp.content, 'html.parser')
        new_jobs = soup.find('div', attrs={'class': 'f-vacancylist-newnotfound'})
        if not new_jobs:
            table = soup.find('table', id='ctl00_content_vacancyList_gridList')
            if table:
                tr_list = table.find_all('tr', attrs={'id': True})
                for tr in tr_list:
                    div = tr.find('div', attrs={'class': 'card-body'})
                    if div:
                        title = div.find('h2', attrs={'class': 'card-title'})
                        href = title.a['href']
                        content = div.p.text
                        company = 'No name'
                        p = div.find('p', attrs={'class': 'company-name'})
                        if p:
                            company = p.a.text
                        jobs.append({'title': title.text, 'url': domain + href,
                                     'description': content, 'company': company})
            else:
                errors.append({'url': url, 'title': "Table does not exists"})
        else:
            errors.append({'url': url, 'title': "Page is empty"})
    else:
        errors.append({'url': url, 'title': "Page not response"})

    return jobs, errors


def dou(url):
    jobs = []
    errors = []
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BS(resp.content, 'html.parser')
        main_div = soup.find('div', id='vacancyListId')
        if main_div:
            li_list = main_div.find_all('li', attrs={'class': 'l-vacancy'})
            for li in li_list:
                title = li.find('div', attrs={'class': 'title'})
                href = title.a['href']
                cont = li.find('div', attrs={'class': 'sh-info'})
                content = cont.text
                company = 'No name'
                a = title.find('a', attrs={'class': 'company'})
                if a:
                    company = a.text
                jobs.append({'title': title.text, 'url': href,
                             'description': content, 'company': company})
        else:
            errors.append({'url': url, 'title': "Div does not exists"})
    else:
        errors.append({'url': url, 'title': "Page not response"})

    return jobs, errors


def djinni(url):
    jobs = []
    errors = []
    domain = 'https://djinni.co'
    try:
        print(f"Trying to fetch data from {url}")
        resp = requests.get(url, headers=headers)
        print(f"Response status code: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            main_ul = soup.find('ul', attrs={'class': 'list-jobs'})
            
            if main_ul:
                li_list = main_ul.find_all('li', attrs={'class': 'list-jobs__item'})
                print(f"Found {len(li_list)} job listings")
                
                for li in li_list:
                    title = li.find('div', attrs={'class': 'list-jobs__title'})
                    if title and title.a:
                        href = title.a['href']
                        cont = li.find('div', attrs={'class': 'list-jobs__description'})
                        content = cont.text if cont else 'No description'
                        company = 'No name'
                        comp = li.find('div', attrs={'class': 'list-details__info'})
                        if comp:
                            company = comp.text
                        jobs.append({
                            'title': title.text.strip(),
                            'url': domain + href,
                            'description': content.strip(),
                            'company': company.strip()
                        })
            else:
                print("Could not find main job list container")
                errors.append({'url': url, 'title': "Main container not found"})
        else:
            print(f"Failed to get response from {url}")
            errors.append({'url': url, 'title': f"Page not response: {resp.status_code}"})
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        errors.append({'url': url, 'title': f"Error: {str(e)}"})

    return jobs, errors
"""

# Placeholder for new job site functions
def example_job_site(url):
    """
    Example function for a new job site.
    Copy this structure when adding new job sites.
    """
    jobs = []
    errors = []
    try:
        print(f"Trying to fetch data from {url}")
        resp = requests.get(url, headers=headers)
        print(f"Response status code: {resp.status_code}")
        
        if resp.status_code == 200:
            # Add your parsing logic here
            pass
        else:
            errors.append({'url': url, 'title': f"Page not response: {resp.status_code}"})
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        errors.append({'url': url, 'title': f"Error: {str(e)}"})

    return jobs, errors


if __name__ == '__main__':
    # Example usage of the placeholder function
    url = 'https://example.com/jobs'
    jobs, errors = example_job_site(url)
    
    # Save jobs to file
    with open('jobs.txt', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    # Print errors if any
    if errors:
        print("\nErrors occurred:")
        for error in errors:
            print(f"- {error['title']} at {error['url']}")
    
    print(f"\nTotal jobs found: {len(jobs)}")