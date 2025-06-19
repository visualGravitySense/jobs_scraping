#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API endpoint CV Keskus IT вакансий
"""

import requests
import json

def test_cvkeskus_api():
    """Тестирование API endpoint для CV Keskus IT вакансий"""
    print("=" * 80)
    print("🔍 Testing CVKeskus IT API endpoint...")
    print("=" * 80)
    
    try:
        # URL для API endpoint
        url = "http://localhost:8000/scraping/api/cvkeskus-it-jobs/"
        
        # Параметры запроса
        params = {
            'limit': 10  # Получаем последние 10 IT вакансий
        }
        
        print(f"Отправляем запрос к: {url}")
        print(f"Параметры: {params}")
        
        # Отправляем GET запрос
        response = requests.get(url, params=params)
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                jobs = data.get('jobs', [])
                count = data.get('count', 0)
                
                print(f"✅ Успешно получено {count} IT вакансий")
                print(f"Источник: {data.get('source')}")
                print(f"Категория: {data.get('category')}")
                
                print(f"\nПоследние {len(jobs)} IT вакансий:")
                for i, job in enumerate(jobs, 1):
                    print(f"{i}. {job.get('title', 'N/A')}")
                    print(f"   Компания: {job.get('company', 'N/A')}")
                    print(f"   Локация: {job.get('location', 'N/A')}")
                    print(f"   Дата: {job.get('posted_date', 'N/A')}")
                    print(f"   URL: {job.get('url', 'N/A')}")
                    print()
                
                # Сохраняем в JSON файл
                with open("cvkeskus_api_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Ответ API сохранен в cvkeskus_api_response.json")
                
                return count
            else:
                print(f"❌ Ошибка API: {data.get('error', 'Unknown error')}")
                return 0
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            return 0
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения. Убедитесь, что Django сервер запущен на localhost:8000")
        return 0
    except Exception as e:
        print(f"❌ Ошибка при тестировании API: {e}")
        return 0

if __name__ == "__main__":
    job_count = test_cvkeskus_api()
    print(f"\n✅ Тест завершен. Получено IT вакансий: {job_count}") 