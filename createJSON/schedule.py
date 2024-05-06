import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from schedule_processing import process_schedule_response
from utils import NoVerifyHTTPAdapter, save_response_to_file, save_request_to_file
import asyncio
from telegram import Update

input_lock = asyncio.Lock()


async def send_telegram_message(bot, update, messages):
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(update.message.chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(update.message.chat_id, text=message_text[i:i+max_message_length])


async def get_input(bot, update, prompt):
    await bot.send_message(chat_id=update.message.chat_id, text=prompt)

    # Получаем временную метку текущего запроса на ввод
    request_time = update.message.date

    while True:
        await asyncio.sleep(1)
        # Захватываем семафор для блокировки остальных операций ввода
        async with input_lock:
            # Получаем только новые обновления после времени последнего запроса
            updates = await bot.get_updates(offset=update.update_id + 1)
            if updates:
                # Фильтруем обновления, оставляя только те, которые появились после запроса пользователя
                new_updates = [u for u in updates if u.message.date > request_time]
                if new_updates:
                    response = new_updates[-1].message.text  # Берем последнее обновление
                    if response is not None and not response.startswith('/'):  # Игнорируем команды
                        return response


async def select_schedule(bot, driver, update):
    select_element_semester = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "semester"))
    )

    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')
    select_element_semester = soup.find('select', {'id': 'semester'})

    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        messages = ["Выберите семестр:"]
        for i, option_semester in enumerate(options_semester[1:], start=1):
            messages.append(f"{i}. {option_semester.text}")

        await send_telegram_message(bot, update, messages)

        selected_semester_index = None
        while selected_semester_index is None:
            user_input = await get_input(bot, update, "Введите номер семестра:")
            if user_input is not None:
                try:
                    selected_semester_index = int(user_input)
                except ValueError:
                    await send_telegram_message(bot, update, ["Некорректный ввод. Введите число."])
            else:
                await send_telegram_message(bot, update, ["Пожалуйста, введите номер семестра."])

        semester_id_mapping = {
            1: 8,
            2: 4,
            3: 3,
            4: 2,
            5: 1
        }

        if selected_semester_index not in semester_id_mapping:
            await send_telegram_message(bot, update, ["Недопустимый номер семестра."])
            return

        selected_semester_id = semester_id_mapping[selected_semester_index]

        user_input = await get_input(bot, update,
                                     "Введите 'student' для расписания студента или 'teacher' для расписания преподавателя: ")

        while user_input.lower() not in ['student', 'teacher']:
            await send_telegram_message(bot, update, ["Неверный ввод. Введите 'student' или 'teacher'."])
            user_input = await get_input(bot, update,
                                         "Введите 'student' для расписания студента или 'teacher' для расписания преподавателя: ")

        if user_input.lower() == 'student':
            data_request = {
                "request": "institute",
                "semester": selected_semester_id
            }

            try:
                response_request = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                 data=data_request)
                response_request.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_request.text)

            if not options_output:
                await send_telegram_message(bot, update, ["На странице нет институтов."])
                return

            messages = ["Выберите институт:"]
            for i, (value, text) in enumerate(options_output, start=1):
                messages.append(f"{i}. {text}")

            await send_telegram_message(bot, update, messages)

            selected_institute_index = None
            while selected_institute_index is None:
                user_input = await get_input(bot, update, "Введите номер института:")
                if user_input is not None:
                    try:
                        selected_institute_index = int(user_input)
                        if selected_institute_index < 1 or selected_institute_index > len(options_output):
                            await send_telegram_message(bot, update, ["Недопустимый номер института."])
                            selected_institute_index = None
                    except ValueError:
                        await send_telegram_message(bot, update, ["Некорректный ввод. Введите число."])
                else:
                    await send_telegram_message(bot, update, ["Пожалуйста, введите номер института."])

            selected_institute = options_output[selected_institute_index - 1][1]
            await send_telegram_message(bot, update, [f"Выбран институт: {selected_institute}"])

            data_speciality = {
                "request": "speciality",
                "semester": selected_semester_id,
                "institute": selected_institute
            }

            try:
                response_speciality = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                     data=data_speciality)
                response_speciality.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_speciality.text)

            if not options_output:
                await send_telegram_message(bot, update, ["На странице нет специальностей."])
                return

            messages = ["Выберите специальность:"]
            for i, (value, text) in enumerate(options_output, start=1):
                messages.append(f"{i}. {text}")

            await send_telegram_message(bot, update, messages)

            selected_speciality_index = None
            while selected_speciality_index is None:
                user_input = await get_input(bot, update, "Введите номер специальности:")
                if user_input is not None:
                    try:
                        selected_speciality_index = int(user_input)
                        if selected_speciality_index < 1 or selected_speciality_index > len(options_output):
                            await send_telegram_message(bot, update, ["Недопустимый номер специальности."])
                            selected_speciality_index = None
                    except ValueError:
                        await send_telegram_message(bot, update, ["Некорректный ввод. Введите число."])
                else:
                    await send_telegram_message(bot, update, ["Пожалуйста, введите номер специальности."])

            selected_speciality = options_output[selected_speciality_index - 1][1]
            await send_telegram_message(bot, update, [f"Выбрана специальность: {selected_speciality}"])

            data_group = {
                "request": "group",
                "semester": selected_semester_id,
                "institute": selected_institute,
                "speciality": selected_speciality
            }

            try:
                response_group = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                               data=data_group)
                response_group.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_group.text)

            if not options_output:
                await send_telegram_message(bot, update, ["На странице нет групп."])
                return

            messages = ["Выберите группу:"]
            for i, (value, text) in enumerate(options_output, start=1):
                messages.append(f"{i}. {text}")

            await send_telegram_message(bot, update, messages)

            selected_group_index = None
            while selected_group_index is None:
                user_input = await get_input(bot, update, "Введите номер группы:")
                if user_input is not None:
                    try:
                        selected_group_index = int(user_input)
                        if selected_group_index < 1 or selected_group_index > len(options_output):
                            await send_telegram_message(bot, update, ["Недопустимый номер группы."])
                            selected_group_index = None
                    except ValueError:
                        await send_telegram_message(bot, update, ["Некорректный ввод. Введите число."])
                else:
                    await send_telegram_message(bot, update, ["Пожалуйста, введите номер группы."])

            selected_group = options_output[selected_group_index - 1][1]
            await send_telegram_message(bot, update, [f"Выбрана группа: {selected_group}"])

            data_schedule = {
                "request": "stimetable",
                "semester": selected_semester_id,
                "institute": selected_institute,
                "speciality": selected_speciality,
                "group": selected_group
            }

            try:
                response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                   data=data_schedule)
                response_schedule.raise_for_status()

                # Сохраняем запрос и ответ
                save_request_to_file(update, response_schedule.request)
                save_response_to_file(update, response_schedule)

                return process_schedule_response(response_schedule, selected_semester_id,
                                                 institute=selected_institute,
                                                 speciality=selected_speciality,
                                                 group=selected_group)
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

        elif user_input.lower() == 'teacher':
            data_request = {
                "request": "teacher",
                "semester": selected_semester_id
            }

            try:
                response_request = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                 data=data_request)
                response_request.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_request.text)

            if not options_output:
                await send_telegram_message(bot, update, ["На странице нет преподавателей."])
                return

            messages = ["Выберите преподавателя:"]
            for i, (value, text) in enumerate(options_output, start=1):
                messages.append(f"{i}. {text}")

            await send_telegram_message(bot, update, messages)

            selected_teacher_index = None
            while selected_teacher_index is None:
                user_input = await get_input(bot, update, "Введите номер преподавателя:")
                if user_input is not None:
                    try:
                        selected_teacher_index = int(user_input)
                        if selected_teacher_index < 1 or selected_teacher_index > len(options_output):
                            await send_telegram_message(bot, update, ["Недопустимый номер преподавателя."])
                            selected_teacher_index = None
                    except ValueError:
                        await send_telegram_message(bot, update, ["Некорректный ввод. Введите число."])
                else:
                    await send_telegram_message(bot, update, ["Пожалуйста, введите номер преподавателя."])

            selected_teacher = options_output[selected_teacher_index - 1][1]
            await send_telegram_message(bot, update, [f"Выбран преподаватель: {selected_teacher}"])

            data_schedule = {
                "request": "ttimetable",
                "semester": selected_semester_id,
                "teacher": selected_teacher
            }

            try:
                response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                   data=data_schedule)
                response_schedule.raise_for_status()

                # Сохраняем запрос и ответ
                save_request_to_file(update, response_schedule.request)
                save_response_to_file(update, response_schedule)

                return process_schedule_response(response_schedule, selected_semester_id,
                                                 teacher=selected_teacher)
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, update, [f"Ошибка запроса: {e}"])
                return

