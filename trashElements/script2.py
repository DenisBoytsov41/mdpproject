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

        # Выводим текст всех option семестра
        print("Выберите семестр:")
        for i, option_semester in enumerate(options_semester, start=1):
            print(f"{i}. {option_semester.text}")

        # Пользователь выбирает семестр
        selected_semester_index = int(input("Введите номер семестра: "))
        selected_semester = options_semester[selected_semester_index - 1].text

        # Собираем данные для отправки на сервер с выбранным семестром
        data_semester = {
            "result": 0,
            "method": "wsm.sessionActivated",
            "parameters": json.dumps({
                "title": "КГУ - расписание занятий",
                "activatedState": 1,
                "semester": selected_semester
            })
        }

        # Отправка запроса на сервер
        session_semester = requests.Session()
        session_semester.mount('https://', NoVerifyHTTPAdapter())
        response_semester = session_semester.post("https://timetable.ksu.edu.ru/", data=data_semester)

        # Обработка ответа сервера для института
        if response_semester.status_code == 200:
            # Ждем, пока элемент будет доступен в DOM
            select_element_institute = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "institute"))
            )

            html_content_institute = response_semester.text
            soup_institute = BeautifulSoup(html_content_institute, 'html.parser')
            select_element_institute = soup_institute.find('select', {'id': 'institute'})

            # Выводим текст всех option института
            options_institute = select_element_institute.find_all('option')
            print("Выберите институт:")
            for i, option_institute in enumerate(options_institute, start=1):
                print(f"{i}. {option_institute.text}")

            # Пользователь выбирает институт
            selected_institute_index = int(input("Введите номер института: "))
            selected_institute = options_institute[selected_institute_index - 1].text

            # Собираем данные для отправки на сервер с выбранным институтом
            data_institute = {
                "result": 0,
                "method": "wsm.sessionActivated",
                "parameters": json.dumps({
                    "title": "КГУ - расписание занятий",
                    "activatedState": 1,
                    "semester": selected_semester,
                    "institute": selected_institute
                })
            }

            # Отправка запроса на сервер для института
            session_institute = requests.Session()
            session_institute.mount('https://', NoVerifyHTTPAdapter())
            response_institute = session_institute.post("https://timetable.ksu.edu.ru/", data=data_institute)

            # Обработка ответа сервера для специальности
            if response_institute.status_code == 200:
                # Ждем, пока элемент будет доступен в DOM
                select_element_speciality = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "speciality"))
                )

                html_content_speciality = response_institute.text
                soup_speciality = BeautifulSoup(html_content_speciality, 'html.parser')
                select_element_speciality = soup_speciality.find('select', {'id': 'speciality'})

                # Выводим текст всех option специальности
                options_speciality = select_element_speciality.find_all('option')
                print("Выберите специальность:")
                for i, option_speciality in enumerate(options_speciality, start=1):
                    print(f"{i}. {option_speciality.text}")

                # Пользователь выбирает специальность
                selected_speciality_index = int(input("Введите номер специальности: "))
                selected_speciality = options_speciality[selected_speciality_index - 1].text

                # Собираем данные для отправки на сервер с выбранной специальностью
                data_speciality = {
                    "result": 0,
                    "method": "wsm.sessionActivated",
                    "parameters": json.dumps({
                        "title": "КГУ - расписание занятий",
                        "activatedState": 1,
                        "semester": selected_semester,
                        "institute": selected_institute,
                        "speciality": selected_speciality
                    })
                }

                # Отправка запроса на сервер для специальности
                session_speciality = requests.Session()
                session_speciality.mount('https://', NoVerifyHTTPAdapter())
                response_speciality = session_speciality.post("https://timetable.ksu.edu.ru/", data=data_speciality)

                # Обработка ответа сервера для группы
                if response_speciality.status_code == 200:
                    # Ждем, пока элемент будет доступен в DOM
                    select_element_group = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "group"))
                    )

                    html_content_group = response_speciality.text
                    soup_group = BeautifulSoup(html_content_group, 'html.parser')
                    select_element_group = soup_group.find('select', {'id': 'group'})

                    # Выводим текст всех option группы
                    options_group = select_element_group.find_all('option')
                    print("Выберите группу:")
                    for i, option_group in enumerate(options_group, start=1):
                        print(f"{i}. {option_group.text}")

                    # Пользователь выбирает группу
                    selected_group_index = int(input("Введите номер группы: "))
                    selected_group = options_group[selected_group_index - 1].text

                    # Собираем данные для отправки на сервер с выбранной группой
                    data_group = {
                        "result": 0,
                        "method": "wsm.sessionActivated",
                        "parameters": json.dumps({
                            "title": "КГУ - расписание занятий",
                            "activatedState": 1,
                            "semester": selected_semester,
                            "institute": selected_institute,
                            "speciality": selected_speciality,
                            "group": selected_group
                        })
                    }

                    # Отправка запроса на сервер для группы
                    session_group = requests.Session()
                    session_group.mount('https://', NoVerifyHTTPAdapter())
                    response_group = session_group.post("https://timetable.ksu.edu.ru/", data=data_group)

                    # Обработка ответа сервера для вывода расписания или других данных
                    if response_group.status_code == 200:
                        print("Получен ответ от сервера для группы:")
                        print(response_group.text)  # Вывести текст ответа перед декодированием

                        try:
                            json_response_group = response_group.json()
                            print("Успешный запрос для группы!")
                            print(json_response_group)  # Вывести ответ в формате jsonAndIcal
                        except requests.exceptions.JSONDecodeError:
                            print("Ошибка декодирования jsonAndIcal или пустой ответ сервера для группы.")
                    else:
                        print(f"Ошибка запроса для группы. Код статуса: {response_group.status_code}")
                        print(response_group.text)  # Вывести текст ошибки, если есть
                else:
                    print(f"Ошибка запроса для специальности. Код статуса: {response_speciality.status_code}")
                    print(response_speciality.text)  # Вывести текст ошибки, если есть
            else:
                print("Ошибка: Не удалось получить HTML-код для специальности.")
        else:
            print(f"Ошибка запроса для института. Код статуса: {response_institute.status_code}")
            print(response_institute.text)  # Вывести текст ошибки, если есть
    else:
        print("Ошибка: Не удалось получить HTML-код для семестра.")

finally:
    # Закрываем браузер после использования
    driver.quit()
