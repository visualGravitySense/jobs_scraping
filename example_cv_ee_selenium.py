import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

def scrape_cv_ee():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Запустите в безголовом режиме, если не нужен GUI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Инициализируем undetected_chromedriver
    driver = uc.Chrome(options=options)

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
        # Ждем загрузки элемента body
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

    # Селекторы для извлечения информации о вакансиях
    # !!! ЭТИ СЕЛЕКТОРЫ НУЖНО БУДЕТ ПРОВЕРИТЬ И ИСПРАВИТЬ ПОСЛЕ АНАЛИЗА page_source.html !!!
    job_cards_selector = '[class*="vacancy-item"]'
    title_selector = '.jsx-3091937985.title'
    company_selector = '.jsx-3091937985.employer'
    location_selector = '.jsx-3091937985.location'

    jobs = []
    print(f"Пробуем селектор: {job_cards_selector}")
    cards = driver.find_elements(By.CSS_SELECTOR, job_cards_selector)
    print(f"Найдено вакансий с селектором {job_cards_selector}: {len(cards)}")

    if not cards:
        print("Не удалось найти элементы вакансий. Возможно, селектор неверный или страница не загрузилась корректно.")
        driver.quit()
        return

    for card in cards:
        try:
            title_element = card.find_element(By.CSS_SELECTOR, title_selector)
            title = title_element.text.strip()
            company_element = card.find_element(By.CSS_SELECTOR, company_selector)
            company = company_element.text.strip()
            location_element = card.find_element(By.CSS_SELECTOR, location_selector)
            location = location_element.text.strip()

            jobs.append({
                'title': title,
                'company': company,
                'location': location
            })
        except Exception as e:
            print(f"Ошибка при парсинге карточки вакансии: {e}")
            continue

    # Сохраняем вакансии в JSON файл
    output_file = 'cv_ee_jobs.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=4)
    print(f"Сохранено вакансий: {len(jobs)} в {output_file}")

    driver.quit()

if __name__ == '__main__':
    scrape_cv_ee() 