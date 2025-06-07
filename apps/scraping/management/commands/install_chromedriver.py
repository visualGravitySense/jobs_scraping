import os
import sys
import zipfile
import requests
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class Command(BaseCommand):
    help = 'Install ChromeDriver for Selenium'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Installing ChromeDriver...'))
        
        try:
            # Установка ChromeDriver с помощью webdriver_manager
            driver_path = ChromeDriverManager().install()
            self.stdout.write(self.style.SUCCESS(f'ChromeDriver installed successfully at: {driver_path}'))
            
            # Проверка установки
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service)
            driver.quit()
            
            self.stdout.write(self.style.SUCCESS('ChromeDriver test successful'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error installing ChromeDriver: {str(e)}'))
            sys.exit(1) 