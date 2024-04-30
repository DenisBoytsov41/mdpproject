import ssl
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class NoVerifyHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLS, **pool_kwargs)

# Инициализация драйвера
driver = webdriver.Chrome()

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
        max_semester = len(options_semester)

        # Выводим текст всех option семестра
        print("Выберите семестр:")
        for i, option_semester in enumerate(options_semester, start=1):
            print(f"{i}. {option_semester.text}")

        # Пользователь выбирает семестр
        selected_semester_index = int(input("Введите номер семестра: "))

        selected_semester = -1

        if 1 <= selected_semester_index <= len(options_semester):
            selected_semester = selected_semester_index - 1
            new_index = max_semester - selected_semester_index + 1
            selected_semester = new_index - 1
            print(f"Выбранный семестр: {selected_semester}")
        else:
            print("Недопустимый номер семестра.")

        # Собираем данные для отправки на сервер с выбранным семестром
        data_open = {
            "result": 0,
            "method": "wsm.sessionActivated",
            "parameters": "{\"title\":\"КГУ - расписание занятий\"}"
        }

        # Сохраняем текст запроса в файл
        with open("open_session_request.txt", "w", encoding="utf-8") as file:
            file.write(json.dumps(data_open, indent=4))

        session_open = requests.Session()
        session_open.mount('https://', NoVerifyHTTPAdapter())
        response_open = session_open.post("https://timetable.ksu.edu.ru/", data=data_open)

        # Сохраняем текст ответа в файл
        with open("open_session_response.txt", "w", encoding="utf-8") as file:
            file.write(response_open.text)

        # Обработка ответа сервера при открытии
        if response_open.status_code == 200:
            print("Успешный запрос при открытии!")
            # Если ответ сервера не является JSON, значит, переходим к следующему этапу
            if not response_open.headers['content-type'].lower().startswith('application/json'):
                # Ждем, пока список институтов будет доступен в DOM
                select_element_institute = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "institute"))
                )
                # Перепарсим HTML после выбора семестра
                html_content_after_semester = driver.page_source
                soup_after_semester = BeautifulSoup(html_content_after_semester, 'html.parser')
                select_element_institute = soup_after_semester.find('select', {'id': 'institute'})

                options_institute = select_element_institute.find_all('option')

                # Выводим текст всех option института
                print("Выберите институт:")
                for i, option_institute in enumerate(options_institute, start=1):
                    print(f"{i}. {option_institute.text}")

                # Пользователь выбирает институт
                selected_institute_index = int(input("Введите номер института: "))

                # Проверяем, чтобы индекс был в допустимых пределах
                if 1 <= selected_institute_index <= len(options_institute):
                    selected_institute = options_institute[selected_institute_index - 1].text
                    print(f"Выбран институт: {selected_institute}")
                else:
                    print("Недопустимый номер института.")

                # Отправляем запрос на сервер с выбранным семестром и институтом
                data_request = {
                    "request": "institute",
                    "semester": selected_semester
                }

                # Сохраняем текст запроса в файл
                with open("institute_request.txt", "w", encoding="utf-8") as file:
                    file.write(json.dumps(data_request, indent=4))

                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                # Сохраняем текст ответа в файл
                with open("institute_response.txt", "w", encoding="utf-8") as file:
                    file.write(response_request.text)

                # Обработка ответа сервера для запроса института
                if response_request.status_code == 200:
                    # Записываем результат запроса в файл
                    with open("output.php", "w", encoding="utf-8") as file:
                        file.write(response_request.text)

                    print("Файл успешно получен и сохранен как output.php.")
                else:
                    print(f"Ошибка запроса для института. Код статуса: {response_request.status_code}")

        else:
            print(f"Ошибка запроса при открытии. Код статуса: {response_open.status_code}")

finally:
    # Отправка запроса на сервер при закрытии
    data_close = {
        "result": 0,
        "method": "wsm.sessionDeactivated",
        "parameters": "{\"title\":\"КГУ - расписание занятий\"}"
    }
    session_close = requests.Session()
    session_close.mount('https://', NoVerifyHTTPAdapter())
    response_close = session_close.post("https://timetable.ksu.edu.ru/", data=data_close)

    # Сохраняем текст ответа в файл
    with open("close_session_response.txt", "w", encoding="utf-8") as file:
        file.write(response_close.text)

    # Закрываем браузер после использования
    driver.quit()
