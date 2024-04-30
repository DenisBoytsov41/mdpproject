import csv
import ssl
import re
import json
import html

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def replace_slash(input_string):
    return input_string.replace("\\/", "/")

def decode_special_chars(data):
    decoded_data_list = []
    for entry in data:
        decoded_entry = {}
        for key, value in entry.items():
            if isinstance(value, str):
                decoded_entry[key] = value.encode('utf-8').decode('unicode_escape')
            else:
                decoded_entry[key] = value
        decoded_data_list.append(decoded_entry)
    return decoded_data_list




def process_schedule_response(response_schedule, semester):
    #semester_id_mapping = {1: 8, 2: 4, 3: 3, 4: 2, 5: 1}
    semester_id_mapping = {8: 1, 4: 2, 3: 3, 2: 4, 1: 5}

    if semester in semester_id_mapping and semester not in [1, 2, 8]:
        if response_schedule.status_code == 200:
            # Записываем результат запроса в файл
            with open("thirdElements/output_schedule.php", "w", encoding="utf-8") as file:
                file.write(response_schedule.text)

            print("Файл успешно получен и сохранен как output_schedule.php.")

            # Загрузить данные из файла
            with open("thirdElements/output_schedule.php", "r", encoding="utf-8") as file:
                content = file.read()

            # Извлечь корректный JSON из строки
            start_index = content.find("[")
            end_index = content.rfind("]") + 1
            json_data = content[start_index:end_index]

            # Преобразовать данные
            data = json.loads(json_data)

            # Маппинг для типов недели
            week_mapping = {"2": "Под чертой", "1": "Над чертой", "0": "Общая"}

            # Маппинг для дней недели
            day_mapping = {"1": "Понедельник", "2": "Вторник", "3": "Среда",
                           "4": "Четверг", "5": "Пятница", "6": "Суббота"}

            # Маппинг для времени пар
            time_mapping = {"1": "8:30 - 10:00", "2": "10:10 - 11:40",
                            "3": "11:50 - 13:20", "4": "14:00 - 15:30",
                            "5": "15:40 - 17:10", "6": "17:20 - 18:50",
                            "7": "19:00 - 20:30"}

            # Преобразовать данные
            processed_data = []
            for entry in data:
                processed_entry = {
                    "День недели": day_mapping.get(entry["x"], entry["x"]),
                    "Время": time_mapping.get(entry["y"], entry["y"]),
                    "Тип недели": week_mapping.get(entry["n"], entry["n"]),
                    "Название предмета": entry["subject1"],
                    "Аудитория": entry["subject2"],
                    "ФИО преподавателя": entry["subject3"],
                    "Тип занятия:": entry["lessontype"],
                    "Группа": entry["subgroup"],
                    "Начало": entry["starttime"],
                    "Конец": entry["endtime"],
                    "Семестр": semester_id_mapping.get(semester)

                }
                processed_data.append(processed_entry)

            # Вывести данные в консоль
            for entry in processed_data:
                print(json.dumps(entry, indent=4, ensure_ascii=False))
                print()

            # Сохранить данные в JSON файл
            output_json_file = "processed_schedule_data.json"
            with open(output_json_file, "w", encoding="utf-8") as json_file:
                json.dump(processed_data, json_file, indent=4,
                          ensure_ascii=False)

            print(
                f"Данные успешно обработаны и сохранены в {output_json_file}.")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")
    else:
        # print("Неверный семестр для обработки.")
        if response_schedule.status_code == 200:
            with open("thirdElements/output_schedule.php", "w", encoding="utf-8") as file:
                file.write(response_schedule.text)

            print("Файл успешно получен и сохранен как output_schedule.php.")
            # Загрузить данные из файла
            with open("thirdElements/output_schedule.php", "r", encoding="utf-8") as file:
                content = file.read()

            content = content.replace("z[[", "").replace("]]", "")

            # Разделить данные на строки
            data_rows = content.split("],[")

            # Преобразование данных в формат JSON
            processed_data = []
            first_row_skipped = False  # Флаг для пропуска первой строки данных
            for row in data_rows:
                if not first_row_skipped:
                    first_row_skipped = True
                    continue  # Пропустить первую строку данных
                values = list(csv.reader([row], delimiter=','))[0]
                if len(values) == 4:
                    day_of_week = html.unescape(values[0].strip('"').split()[1])  # Извлечение только дня недели
                    date_parts = html.unescape(values[0].strip('"').split()[0]).split('.')
                    date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"  # Преобразование формата даты
                    time = html.unescape(values[1].strip('"')).replace("<br />", " ")
                    # Декодирование HTML-спецсимволов

                    values_two = ["".join(values[2])]

                    values_two = [replace_slash(value) for value in values_two]

                    for i in range(len(values)):
                        values[i] = [replace_slash(values[i])]

                    subject_and_teacher = html.unescape(values_two[0].strip('"'))

                    subject_parts = subject_and_teacher.split("<br />")

                    # Извлечение данных
                    subject = subject_parts[0].replace("<b>", "").replace("</b>", "").strip()
                    audience_raw = subject_parts[-1].strip() if len(subject_parts) > 1 else ""
                    teacher = subject_parts[-2].strip() if len(subject_parts) > 2 else ""
                    lesson_type_raw = subject_parts[-3].strip() if len(subject_parts) > 3 else ""

                    lesson_type = lesson_type_raw.replace("<sup><i>", "").replace("</i></sup>", "")

                    processed_row = {
                        "День недели": replace_slash(day_of_week).replace("/>", ""),
                        "Дата": replace_slash(date).replace("<br", ""),
                        "Время": replace_slash(time).replace("<br", "").replace("/>","- "),
                        "Название предмета": replace_slash(subject),
                        "Аудитория": replace_slash(audience_raw),
                        "ФИО преподавателя": replace_slash(teacher),
                        "Тип занятия": replace_slash(lesson_type),
                        "Семестр": semester_id_mapping.get(semester)
                    }

                    processed_data.append(processed_row)
                else:
                    print("Неправильный формат данных:", row)

            processed_data = decode_special_chars(processed_data)
            # Сохранение обработанных данных в JSON файл
            output_json_file = "processed_schedule_data.json"
            with open(output_json_file, "w", encoding="utf-8") as json_file:
                json.dump(processed_data, json_file, indent=4, ensure_ascii=False)


            print(f"Данные успешно обработаны и сохранены в {output_json_file}.")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")


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
    user_input = ""

    # Проверка, что select_element_semester не является None перед вызовом find_all
    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        # Получаем максимальное значение семестра
        max_semester = len(options_semester)

        # Выводим текст всех option семестра
        print("Выберите семестр:")
        for i, option_semester in enumerate(options_semester[1:], start=1):
            print(f"{i}. {option_semester.text}")

        # Пользователь выбирает семестр
        selected_semester_index = int(input("Введите номер семестра:"))

        # Словарь для соответствия выбранного номера семестра и его id
        semester_id_mapping = {
            1: 8,
            2: 4,
            3: 3,
            4: 2,
            5: 1
        }

        selected_semester = -1
        while True:

            if selected_semester_index in semester_id_mapping:
                selected_semester_id = semester_id_mapping[selected_semester_index]
                # Запрос типа расписания у пользователя
                user_input = input("Введите 'student' для расписания студента или 'teacher' для расписания преподавателя: ")
            else:
                print("Недопустимый номер семестра.")
                exit()

            # if 1 <= selected_semester_index <= len(options_semester):
            #     selected_semester = selected_semester_index - 1
            #     new_index = max_semester - selected_semester_index + 1
            #     selected_semester = new_index - 1
            #     print(f"Выбранный семестр: {options_semester[selected_semester].text}")
            # else:
            #     print("Недопустимый номер семестра.")

            selected_semester = selected_semester_id

            if user_input.lower() == 'student':
                data_request = {
                    "request": "institute",
                    "semester": selected_semester
                }
                # Сохраняем текст запроса в файл
                with open("thirdElements/institute_request.txt", "w", encoding="utf-8") as file:
                    file.write(json.dumps(data_request, indent=4))

                # Создается объект сессии session_request из библиотеки requests.
                # Сессия позволяет сохранять состояние между запросами, такие как куки и заголовки.
                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                # Сохраняем текст ответа в файл
                with open("thirdElements/institute_response.txt", "w", encoding="utf-8") as file:
                    file.write(response_request.text)

                # Обработка ответа сервера для запроса института
                if response_request.status_code == 200:
                    # Записываем результат запроса в файл
                    with open("thirdElements/output.php", "w", encoding="utf-8") as file:
                        file.write(response_request.text)

                    print("Файл успешно получен и сохранен как output.php.")

                    # Читаем институты из файла output.php
                    with open("thirdElements/output.php", "r", encoding="utf-8") as file:
                        content = file.read()

                    # Просто используем строку, не оборачиваем в BeautifulSoup, так как это не полноценный HTML-документ
                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                    # Проверяем, есть ли институты
                    if options_output:
                        # Выводим текст всех option института
                        print("Выберите институт:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            print(f"{i}. {text}")

                        # Пользователь выбирает институт
                        selected_institute_index = int(input("Введите номер института: "))

                        # Проверяем, чтобы индекс был в допустимых пределах
                        if 1 <= selected_institute_index <= len(options_output):
                            selected_institute = options_output[selected_institute_index - 1][1]
                            print(f"Выбран институт: {selected_institute}")

                            # Отправляем запрос на сервер с выбранным институтом и семестром
                            data_speciality = {
                                "request": "speciality",
                                "semester": selected_semester,
                                "institute": selected_institute
                            }

                            # Сохраняем текст запроса в файл
                            with open("thirdElements/speciality_request.txt", "w", encoding="utf-8") as file:
                                file.write(json.dumps(data_speciality, indent=4))

                            session_speciality = requests.Session()
                            session_speciality.mount('https://', NoVerifyHTTPAdapter())
                            response_speciality = session_speciality.post("https://timetable.ksu.edu.ru/engine.php",
                                                                          data=data_speciality)

                            # Сохраняем текст ответа в файл
                            with open("thirdElements/speciality_response.txt", "w", encoding="utf-8") as file:
                                file.write(response_speciality.text)

                            # Обработка ответа сервера для запроса специальности
                            if response_speciality.status_code == 200:
                                # Записываем результат запроса в файл
                                with open("thirdElements/output_speciality.php", "w", encoding="utf-8") as file:
                                    file.write(response_speciality.text)

                                print("Файл успешно получен и сохранен как output_speciality.php.")

                                # Читаем специальности из файла output_speciality.php
                                with open("thirdElements/output_speciality.php", "r", encoding="utf-8") as file:
                                    content = file.read()

                                # Просто используем строку, не оборачиваем в BeautifulSoup, так как это не полноценный HTML-документ
                                options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                                if options_output:
                                    # Выводим текст всех option института
                                    print("Выберите специальность:")
                                    for i, (value, text) in enumerate(options_output, start=1):
                                        print(f"{i}. {text}")

                                    # Пользователь выбирает специальность
                                    selected_speciality_index = int(input("Введите номер специальности: "))

                                    # Проверяем, чтобы индекс был в допустимых пределах
                                    if 1 <= selected_speciality_index <= len(options_output):
                                        selected_speciality = options_output[selected_speciality_index - 1][1]
                                        print(f"Выбрана специальность: {selected_speciality}")

                                        # Отправляем запрос на сервер с выбранной специальностью, институтом и семестром
                                        data_group = {
                                            "request": "group",
                                            "semester": selected_semester,
                                            "institute": selected_institute,
                                            "speciality": selected_speciality
                                        }

                                        # Сохраняем текст запроса в файл
                                        with open("thirdElements/group_request.txt", "w", encoding="utf-8") as file:
                                            file.write(json.dumps(data_group, indent=4))

                                        session_group = requests.Session()
                                        session_group.mount('https://', NoVerifyHTTPAdapter())
                                        response_group = session_group.post("https://timetable.ksu.edu.ru/engine.php",
                                                                            data=data_group)

                                        # Сохраняем текст ответа в файл
                                        with open("thirdElements/group_response.txt", "w", encoding="utf-8") as file:
                                            file.write(response_group.text)

                                        # Обработка ответа сервера для запроса группы
                                        if response_group.status_code == 200:
                                            # Записываем результат запроса в файл
                                            with open("thirdElements/output_group.php", "w", encoding="utf-8") as file:
                                                file.write(response_group.text)

                                            print("Файл успешно получен и сохранен как output_group.php.")

                                            # Читаем группы из файла output_group.php
                                            with open("thirdElements/output_group.php", "r", encoding="utf-8") as file:
                                                content = file.read()

                                            # Просто используем строку, не оборачиваем в BeautifulSoup, так как это не полноценный HTML-документ
                                            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                                                        content)

                                            # Проверяем, есть ли группы
                                            if options_output:
                                                # Выводим текст всех option группы
                                                print("Выберите группу:")
                                                for i, (value, text) in enumerate(options_output, start=1):
                                                    print(f"{i}. {text}")

                                                # Пользователь выбирает группу
                                                selected_group_index = int(input("Введите номер группы: "))

                                                # Проверяем, чтобы индекс был в допустимых пределах
                                                if 1 <= selected_group_index <= len(options_output):
                                                    selected_group = options_output[selected_group_index - 1][1]
                                                    print(f"Выбрана группа: {selected_group}")

                                                    # Отправляем запрос на сервер с выбранной группой, специальностью, институтом и семестром
                                                    data_schedule = {
                                                        "request": "stimetable",
                                                        "semester": selected_semester,
                                                        "institute": selected_institute,
                                                        "speciality": selected_speciality,
                                                        "group": selected_group
                                                    }

                                                    # Сохраняем текст запроса в файл
                                                    with open("thirdElements/schedule_request.txt", "w", encoding="utf-8") as file:
                                                        file.write(json.dumps(data_schedule, indent=4))

                                                    session_schedule = requests.Session()
                                                    session_schedule.mount('https://', NoVerifyHTTPAdapter())
                                                    response_schedule = session_schedule.post(
                                                        "https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                                                    # Сохраняем текст ответа в файл
                                                    with open("thirdElements/schedule_response.txt", "w", encoding="utf-8") as file:
                                                        file.write(response_schedule.text)

                                                    process_schedule_response(response_schedule,selected_semester)

                                                else:
                                                    print("Недопустимый номер группы.")
                                            else:
                                                print("На странице нет групп.")
                                        else:
                                            print(f"Ошибка запроса для группы. Код статуса: {response_group.status_code}")

                                    else:
                                        print("Недопустимый номер специальности.")
                                else:
                                    print("На странице нет специальностей.")

                            else:
                                print(f"Ошибка запроса для специальности. Код статуса: {response_speciality.status_code}")

                        else:
                            print("Недопустимый номер института.")
                    else:
                        print("На странице нет институтов.")

                else:
                    print(f"Ошибка запроса для института. Код статуса: {response_request.status_code}")
                break

            elif user_input.lower() == 'teacher':
                data_request = {
                    "request": "teacher",
                    "semester": selected_semester
                }
                # Сохраняем текст запроса в файл
                with open("thirdElements/teacher_request.txt", "w", encoding="utf-8") as file:
                    file.write(json.dumps(data_request, indent=4))

                # Создается объект сессии session_request из библиотеки requests.
                # Сессия позволяет сохранять состояние между запросами, такие как куки и заголовки.
                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                # Сохраняем текст ответа в файл
                with open("thirdElements/teacher_response.txt", "w", encoding="utf-8") as file:
                    file.write(response_request.text)

                # Обработка ответа сервера для запроса института
                if response_request.status_code == 200:
                    # Записываем результат запроса в файл
                    with open("thirdElements/output_teacher.php", "w", encoding="utf-8") as file:
                        file.write(response_request.text)

                    print("Файл успешно получен и сохранен как output.php.")

                    # Читаем институты из файла output.php
                    with open("thirdElements/output_teacher.php", "r", encoding="utf-8") as file:
                        content = file.read()

                    # Просто используем строку, не оборачиваем в BeautifulSoup, так как это не полноценный HTML-документ
                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                    # Проверяем, есть ли институты
                    if options_output:
                        # Выводим текст всех option института
                        print("Выберите преподавателя:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            print(f"{i}. {text}")

                        # Пользователь выбирает институт
                        selected_institute_index = int(input("Введите номер преподавателя: "))

                        # Проверяем, чтобы индекс был в допустимых пределах
                        if 1 <= selected_institute_index <= len(options_output):
                            selected_institute = options_output[selected_institute_index - 1][1]
                            print(f"Выбран преподаватель: {selected_institute}")

                            # Отправляем запрос на сервер с выбранным институтом и семестром
                            data_schedule = {
                                "request": "ttimetable",
                                "semester": selected_semester,
                                "teacher": selected_institute
                            }
                            # Сохраняем текст запроса в файл
                            with open("thirdElements/schedule_request.txt", "w", encoding="utf-8") as file:
                                file.write(json.dumps(data_schedule, indent=4))

                            session_schedule = requests.Session()
                            session_schedule.mount('https://', NoVerifyHTTPAdapter())
                            response_schedule = session_schedule.post(
                                "https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                            # Сохраняем текст ответа в файл
                            with open("thirdElements/schedule_response.txt", "w", encoding="utf-8") as file:
                                file.write(response_schedule.text)

                            process_schedule_response(response_schedule,selected_semester)
                break
            elif user_input.lower() != 'student' and user_input.lower() != 'teacher':
                print("Неверный ввод. Введите 'student' или 'teacher'.")


finally:
    # Закрываем браузер после использования
    driver.quit()
