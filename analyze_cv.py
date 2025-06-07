import requests
from bs4 import BeautifulSoup
import json

def analyze_cv_ee():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,et;q=0.8',
        'Connection': 'keep-alive',
    }

    api_endpoints = [
        'https://cv.ee/api/v1/job-ads',
        'https://www.cv.ee/api/v1/job-ads',
        'https://cv.ee/et/api/job-offers',
        'https://www.cv.ee/et/api/job-offers',
        'https://cv.ee/et/api/vacancies',
        'https://www.cv.ee/et/api/vacancies',
        'https://cv.ee/api/vacancies',
        'https://www.cv.ee/api/vacancies',
    ]

    for url in api_endpoints:
        print(f"\nTrying API endpoint: {url}")
        try:
            resp = requests.get(url, headers=headers)
            print(f"Status code: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    print(f"Sample: {str(data)[:500]}\n...")
                except Exception as e:
                    print(f"Could not parse JSON: {e}")
                    print(f"Raw content: {resp.text[:500]}\n...")
            else:
                print(f"Response: {resp.text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    analyze_cv_ee() 