import json
import os
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from schedule_processing import process_schedule_response
from utils import NoVerifyHTTPAdapter

def select_schedule(driver):
    select_element_semester = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "semester"))
    )

    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')
    select_element_semester = soup.find('select', {'id': 'semester'})
    user_input = ""

    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        max_semester = len(options_semester)

        print("Выберите семестр:")
        for i, option_semester in enumerate(options_semester[1:], start=1):
            print(f"{i}. {option_semester.text}")

        selected_semester_index = int(input("Введите номер семестра:"))

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
                user_input = input(
                    "Введите 'student' для расписания студента или 'teacher' для расписания преподавателя: ")
            else:
                print("Недопустимый номер семестра.")
                exit()

            selected_semester = selected_semester_id

            if user_input.lower() == 'student':
                data_request = {
                    "request": "institute",
                    "semester": selected_semester
                }
                # Сохраняем текст запроса в файл
                inst_file_path = os.path.join("..", "thirdElements", "institute_request.txt")
                with open(inst_file_path, "w", encoding="utf-8") as file:
                    file.write(json.dumps(data_request, indent=4))

                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                instres_file_path = os.path.join("..", "thirdElements", "institute_response.txt")
                with open(instres_file_path, "w", encoding="utf-8") as file:
                    file.write(response_request.text)

                if response_request.status_code == 200:
                    output_file_path = os.path.join("..", "thirdElements", "output.php")
                    with open(output_file_path, "w", encoding="utf-8") as file:
                        file.write(response_request.text)

                    print("Файл успешно получен и сохранен как output.php.")

                    with open(output_file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                    if options_output:
                        print("Выберите институт:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            print(f"{i}. {text}")

                        selected_institute_index = int(input("Введите номер института: "))

                        if 1 <= selected_institute_index <= len(options_output):
                            selected_institute = options_output[selected_institute_index - 1][1]
                            print(f"Выбран институт: {selected_institute}")

                            data_speciality = {
                                "request": "speciality",
                                "semester": selected_semester,
                                "institute": selected_institute
                            }

                            speciality_file_path = os.path.join("..", "thirdElements", "speciality_request.txt")
                            with open(speciality_file_path, "w", encoding="utf-8") as file:
                                file.write(json.dumps(data_speciality, indent=4))

                            session_speciality = requests.Session()
                            session_speciality.mount('https://', NoVerifyHTTPAdapter())
                            response_speciality = session_speciality.post("https://timetable.ksu.edu.ru/engine.php",
                                                                          data=data_speciality)

                            specres_file_path = os.path.join("..", "thirdElements", "speciality_response.txt")
                            with open(specres_file_path, "w", encoding="utf-8") as file:
                                file.write(response_speciality.text)

                            if response_speciality.status_code == 200:
                                output_speciality_file_path = os.path.join("..", "thirdElements", "output_speciality.php")
                                with open(output_speciality_file_path, "w", encoding="utf-8") as file:
                                    file.write(response_speciality.text)

                                print("Файл успешно получен и сохранен как output_speciality.php.")

                                with open(output_speciality_file_path, "r", encoding="utf-8") as file:
                                    content = file.read()

                                options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                                if options_output:
                                    print("Выберите специальность:")
                                    for i, (value, text) in enumerate(options_output, start=1):
                                        print(f"{i}. {text}")

                                    selected_speciality_index = int(input("Введите номер специальности: "))

                                    if 1 <= selected_speciality_index <= len(options_output):
                                        selected_speciality = options_output[selected_speciality_index - 1][1]
                                        print(f"Выбрана специальность: {selected_speciality}")

                                        data_group = {
                                            "request": "group",
                                            "semester": selected_semester,
                                            "institute": selected_institute,
                                            "speciality": selected_speciality
                                        }

                                        group_file_path = os.path.join("..", "thirdElements","group_request.txt")
                                        with open(group_file_path, "w", encoding="utf-8") as file:
                                            file.write(json.dumps(data_group, indent=4))

                                        session_group = requests.Session()
                                        session_group.mount('https://', NoVerifyHTTPAdapter())
                                        response_group = session_group.post("https://timetable.ksu.edu.ru/engine.php",
                                                                            data=data_group)

                                        group_response_file_path = os.path.join("..", "thirdElements", "group_response.txt")
                                        with open(group_response_file_path, "w", encoding="utf-8") as file:
                                            file.write(response_group.text)

                                        if response_group.status_code == 200:
                                            output_group_file_path = os.path.join("..", "thirdElements",
                                                                                    "output_group.php")
                                            with open(output_group_file_path, "w", encoding="utf-8") as file:
                                                file.write(response_group.text)

                                            print("Файл успешно получен и сохранен как output_group.php.")

                                            with open(output_group_file_path, "r", encoding="utf-8") as file:
                                                content = file.read()

                                            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                                                        content)

                                            if options_output:
                                                print("Выберите группу:")
                                                for i, (value, text) in enumerate(options_output, start=1):
                                                    print(f"{i}. {text}")

                                                selected_group_index = int(input("Введите номер группы: "))

                                                if 1 <= selected_group_index <= len(options_output):
                                                    selected_group = options_output[selected_group_index - 1][1]
                                                    print(f"Выбрана группа: {selected_group}")

                                                    data_schedule = {
                                                        "request": "stimetable",
                                                        "semester": selected_semester,
                                                        "institute": selected_institute,
                                                        "speciality": selected_speciality,
                                                        "group": selected_group
                                                    }

                                                    schedule_file_path = os.path.join("..", "thirdElements",
                                                                                          "schedule_request.txt")
                                                    with open(schedule_file_path, "w",
                                                              encoding="utf-8") as file:
                                                        file.write(json.dumps(data_schedule, indent=4))

                                                    session_schedule = requests.Session()
                                                    session_schedule.mount('https://', NoVerifyHTTPAdapter())
                                                    response_schedule = session_schedule.post(
                                                        "https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                                                    schedule_response_file_path = os.path.join("..", "thirdElements",
                                                                                      "schedule_response.txt")
                                                    with open(schedule_response_file_path, "w",
                                                              encoding="utf-8") as file:
                                                        file.write(response_schedule.text)

                                                    process_schedule_response(response_schedule, selected_semester)

                                                else:
                                                    print("Недопустимый номер группы.")
                                            else:
                                                print("На странице нет групп.")
                                        else:
                                            print(
                                                f"Ошибка запроса для группы. Код статуса: {response_group.status_code}")

                                    else:
                                        print("Недопустимый номер специальности.")
                                else:
                                    print("На странице нет специальностей.")

                            else:
                                print(
                                    f"Ошибка запроса для специальности. Код статуса: {response_speciality.status_code}")

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
                teacher_file_path = os.path.join("..", "thirdElements", "teacher_request.txt")
                with open(teacher_file_path, "w", encoding="utf-8") as file:
                    file.write(json.dumps(data_request, indent=4))

                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                teacher_response_file_path = os.path.join("..", "thirdElements", "teacher_response.txt")
                with open(teacher_response_file_path, "w", encoding="utf-8") as file:
                    file.write(response_request.text)

                if response_request.status_code == 200:
                    output_teacher_response_file_path = os.path.join("..", "thirdElements", "output_teacher.php")
                    with open(output_teacher_response_file_path, "w", encoding="utf-8") as file:
                        file.write(response_request.text)

                    print("Файл успешно получен и сохранен как output.php.")

                    with open(output_teacher_response_file_path, "r", encoding="utf-8") as file:
                        content = file.read()

                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', content)

                    if options_output:
                        print("Выберите преподавателя:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            print(f"{i}. {text}")

                        selected_institute_index = int(input("Введите номер преподавателя: "))

                        if 1 <= selected_institute_index <= len(options_output):
                            selected_institute = options_output[selected_institute_index - 1][1]
                            print(f"Выбран преподаватель: {selected_institute}")

                            data_schedule = {
                                "request": "ttimetable",
                                "semester": selected_semester,
                                "teacher": selected_institute
                            }
                            # Сохраняем текст запроса в файл
                            schedule_request_file_path = os.path.join("..", "thirdElements",
                                                                             "schedule_request.txt")
                            with open(schedule_request_file_path, "w", encoding="utf-8") as file:
                                file.write(json.dumps(data_schedule, indent=4))

                            session_schedule = requests.Session()
                            session_schedule.mount('https://', NoVerifyHTTPAdapter())
                            response_schedule = session_schedule.post(
                                "https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                            schedule_response_file_path = os.path.join("..", "thirdElements",
                                                                      "schedule_response.txt")
                            with open(schedule_response_file_path, "w", encoding="utf-8") as file:
                                file.write(response_schedule.text)

                            process_schedule_response(response_schedule, selected_semester)
                break
            elif user_input.lower() != 'student' and user_input.lower() != 'teacher':
                print("Неверный ввод. Введите 'student' или 'teacher'.")

