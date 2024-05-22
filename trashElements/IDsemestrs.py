import ssl
import re
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class NoVerifyHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLS, **pool_kwargs)


service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)


valid_semesters = []  # Список для хранения семестров с не пустыми запросами

try:
    # Загрузка страницы
    driver.get("https://timetable.ksu.edu.ru/")

    # Ждем, пока элемент будет доступен в DOM
    select_element_semester = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "semester"))
    )

    # Получаем HTML-код после выполнения JavaScript
    html_content = driver.page_source

    # Парсинг HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    select_element_semester = soup.find('select', {'id': 'semester'})

    # Проверка, что select_element_semester не является None перед вызовом find_all
    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        # Получаем максимальное значение семестра
        max_semester = 20

        # Перебираем все семестры от 1 до max_semester
        for selected_semester in range(1, max_semester + 1):
            data_request = {
                "request": "institute",
                "semester": selected_semester
            }

            # Создается объект сессии session_request из библиотеки requests.
            # Сессия позволяет сохранять состояние между запросами, такие как куки и заголовки.
            session_request = requests.Session()
            session_request.mount('https://', NoVerifyHTTPAdapter())
            response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

            # Обработка ответа сервера для запроса института
            if response_request.status_code == 200 and response_request.text.strip() != "":
                valid_semesters.append(selected_semester)

finally:
    # Закрываем браузер после использования
    driver.quit()

# Вывод списка семестров
print("Список семестров с не пустыми запросами:")
for semester in valid_semesters:
    print(semester)
