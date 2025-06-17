import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup  # NEW: for parsing HTML

def scrape_cv_ee():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Запустите в безголовом режиме, если не нужен GUI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Инициализируем Chrome с webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # Устанавливаем размер окна
    driver.set_window_size(1920, 1080)

    url = 'https://cv.ee/et/search?limit=20&offset=0&categories%5B0%5D=INFORMATION_TECHNOLOGY&towns%5B0%5D=312&fuzzy=true&searchId=5a669240-aba6-45c6-aa12-025e6e9b6502'
    print(f"Открываем страницу: {url}")
    driver.get(url)

    # Добавляем обработку куки-баннера
    try:
        print("Ожидаем появления баннера согласия на использование файлов cookie...")
        accept_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Nõustun kõigiga')]"))
        )
        accept_button.click()
        print("Баннер согласия на использование файлов cookie принят.")
        time.sleep(2)  # Небольшая задержка после принятия куки
    except Exception as e:
        print(f"Не удалось найти или нажать кнопку согласия на использование файлов cookie: {e}")

    # Ждем загрузки страницы с вакансиями
    try:
        print("Ожидаем появления объявлений о вакансиях...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        time.sleep(5) # Дополнительная задержка для динамической загрузки контента
        print("Объявления о вакансиях загружены.")
    except Exception as e:
        print(f"Не удалось найти объявления о вакансиях: {e}")
        with open('page_source_after_load_fail.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("HTML сохранен в page_source_after_load_fail.html")
        driver.quit()
        return

    # Прокручиваем страницу для загрузки всех вакансий (если они загружаются при прокрутке)
    print("Прокручиваем страницу...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Даем время на загрузку нового контента
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print("Прокрутка завершена.")

    # Сохраняем HTML страницы после загрузки и прокрутки
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("Исходный код страницы сохранен в page_source.html")

    # --- NEW: Extract job data from embedded JSON ---
    print("Извлекаем вакансии из JSON внутри <script id=__NEXT_DATA__> ...")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("Не найден тег <script id=__NEXT_DATA__>!")
        driver.quit()
        return
    try:
        data = json.loads(script_tag.string)
        vacancies = data["props"]["pageProps"]["searchResults"]["vacancies"]
    except Exception as e:
        print(f"Ошибка при разборе JSON: {e}")
        driver.quit()
        return

    jobs = []
    for job in vacancies:
        jobs.append({
            'title': job.get('positionTitle'),
            'company': job.get('employerName'),
            'location': job.get('townId'),  # townId is a number, you may want to map it to a name
            'salaryFrom': job.get('salaryFrom'),
            'salaryTo': job.get('salaryTo'),
            'remoteWork': job.get('remoteWork'),
            'publishDate': job.get('publishDate'),
            'expirationDate': job.get('expirationDate'),
            'description': job.get('positionContent'),
            'id': job.get('id'),
            'employerId': job.get('employerId'),
        })

    # Сохраняем вакансии в JSON файл
    output_file = 'cv_ee_jobs.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=4)
    print(f"Сохранено вакансий: {len(jobs)} в {output_file}")

    driver.quit()

if __name__ == '__main__':
    scrape_cv_ee() 