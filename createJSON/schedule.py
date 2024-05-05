import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from schedule_processing import process_schedule_response
from utils import NoVerifyHTTPAdapter, save_response_to_file, save_request_to_file
from telegram import Update

async def send_telegram_message(bot, update, message):
    await bot.send_message(update.message.chat_id, text=message)

async def get_input(bot, update, prompt):
    await bot.send_message(chat_id=update.message.chat_id, text=prompt)
    updates = await bot.get_updates()
    response = updates[-1].message.text  # Берем последнее обновление
    return response




async def select_schedule(bot, driver, update):
    select_element_semester = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "semester"))
    )

    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')
    select_element_semester = soup.find('select', {'id': 'semester'})
    user_input = ""

    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        await send_telegram_message(bot, update, "Выберите семестр:")
        for i, option_semester in enumerate(options_semester[1:], start=1):
            await send_telegram_message(bot, update, f"{i}. {option_semester.text}")

        selected_semester_index = int(await get_input(bot, update, "Введите номер семестра:"))

        semester_id_mapping = {
            1: 8,
            2: 4,
            3: 3,
            4: 2,
            5: 1
        }

        if selected_semester_index not in semester_id_mapping:
            await send_telegram_message(bot, update, "Недопустимый номер семестра.")
            return

        selected_semester_id = semester_id_mapping[selected_semester_index]

        while True:
            user_input = await get_input(bot, update, "Введите 'student' для расписания студента или 'teacher' для расписания преподавателя: ")

            if user_input.lower() == 'student':
                data_request = {
                    "request": "institute",
                    "semester": selected_semester_id
                }

                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                if response_request.status_code == 200:
                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_request.text)

                    if options_output:
                        await send_telegram_message(bot, update, "Выберите институт:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            await send_telegram_message(bot, update, f"{i}. {text}")

                        selected_institute_index = int(await get_input(bot, update, "Введите номер института: "))

                        if 1 <= selected_institute_index <= len(options_output):
                            selected_institute = options_output[selected_institute_index - 1][1]
                            await send_telegram_message(bot, update, f"Выбран институт: {selected_institute}")

                            data_speciality = {
                                "request": "speciality",
                                "semester": selected_semester_id,
                                "institute": selected_institute
                            }

                            session_speciality = requests.Session()
                            session_speciality.mount('https://', NoVerifyHTTPAdapter())
                            response_speciality = session_speciality.post("https://timetable.ksu.edu.ru/engine.php", data=data_speciality)

                            if response_speciality.status_code == 200:
                                options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_speciality.text)

                                if options_output:
                                    await send_telegram_message(bot, update, "Выберите специальность:")
                                    for i, (value, text) in enumerate(options_output, start=1):
                                        await send_telegram_message(bot, update, f"{i}. {text}")

                                    selected_speciality_index = int(await get_input(bot, update, "Введите номер специальности: "))

                                    if 1 <= selected_speciality_index <= len(options_output):
                                        selected_speciality = options_output[selected_speciality_index - 1][1]
                                        await  send_telegram_message(bot, update, f"Выбрана специальность: {selected_speciality}")

                                        data_group = {
                                            "request": "group",
                                            "semester": selected_semester_id,
                                            "institute": selected_institute,
                                            "speciality": selected_speciality
                                        }

                                        session_group = requests.Session()
                                        session_group.mount('https://', NoVerifyHTTPAdapter())
                                        response_group = session_group.post("https://timetable.ksu.edu.ru/engine.php", data=data_group)

                                        if response_group.status_code == 200:
                                            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_group.text)

                                            if options_output:
                                                await send_telegram_message(bot, update, "Выберите группу:")
                                                for i, (value, text) in enumerate(options_output, start=1):
                                                    await send_telegram_message(bot, update, f"{i}. {text}")

                                                selected_group_index = int(await get_input(bot, update, "Введите номер группы: "))

                                                if 1 <= selected_group_index <= len(options_output):
                                                    selected_group = options_output[selected_group_index - 1][1]
                                                    await send_telegram_message(bot, update, f"Выбрана группа: {selected_group}")

                                                    data_schedule = {
                                                        "request": "stimetable",
                                                        "semester": selected_semester_id,
                                                        "institute": selected_institute,
                                                        "speciality": selected_speciality,
                                                        "group": selected_group
                                                    }

                                                    session_schedule = requests.Session()
                                                    session_schedule.mount('https://', NoVerifyHTTPAdapter())
                                                    response_schedule = session_schedule.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                                                    # Сохраняем запрос и ответ
                                                    save_request_to_file(update, response_schedule.request)
                                                    save_response_to_file(update, response_schedule)

                                                    return process_schedule_response(response_schedule, selected_semester_id, institute=selected_institute, speciality=selected_speciality, group=selected_group)

                                                else:
                                                    await send_telegram_message(bot, update, "Недопустимый номер группы.")
                                            else:
                                                await send_telegram_message(bot, update, "На странице нет групп.")
                                        else:
                                            await send_telegram_message(bot, update, f"Ошибка запроса для группы. Код статуса: {response_group.status_code}")

                                    else:
                                        await send_telegram_message(bot, update, "Недопустимый номер специальности.")
                                else:
                                    await send_telegram_message(bot, update, "На странице нет специальностей.")

                            else:
                                await send_telegram_message(bot, update, f"Ошибка запроса для специальности. Код статуса: {response_speciality.status_code}")

                        else:
                            await send_telegram_message(bot, update, "Недопустимый номер института.")
                    else:
                        await send_telegram_message(bot, update, "На странице нет институтов.")

                else:
                    await send_telegram_message(bot, update, f"Ошибка запроса для института. Код статуса: {response_request.status_code}")
                break

            elif user_input.lower() == 'teacher':
                data_request = {
                    "request": "teacher",
                    "semester": selected_semester_id
                }

                session_request = requests.Session()
                session_request.mount('https://', NoVerifyHTTPAdapter())
                response_request = session_request.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)

                if response_request.status_code == 200:
                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_request.text)

                    if options_output:
                        await send_telegram_message(bot, update, "Выберите преподавателя:")
                        for i, (value, text) in enumerate(options_output, start=1):
                            await send_telegram_message(bot, update, f"{i}. {text}")

                        selected_teacher_index = int(await get_input(bot, update, "Введите номер преподавателя: "))

                        if 1 <= selected_teacher_index <= len(options_output):
                            selected_teacher = options_output[selected_teacher_index - 1][1]
                            await send_telegram_message(bot, update, f"Выбран преподаватель: {selected_teacher}")

                            data_schedule = {
                                "request": "ttimetable",
                                "semester": selected_semester_id,
                                "teacher": selected_teacher
                            }

                            session_schedule = requests.Session()
                            session_schedule.mount('https://', NoVerifyHTTPAdapter())
                            response_schedule = session_schedule.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)

                            # Сохраняем запрос и ответ
                            save_request_to_file(update, response_schedule.request)
                            save_response_to_file(update, response_schedule)

                            return process_schedule_response(response_schedule, selected_semester_id, teacher=selected_teacher)
                break
            elif user_input.lower() != 'student' and user_input.lower() != 'teacher':
                await send_telegram_message(bot, update, "Неверный ввод. Введите 'student' или 'teacher'.")
