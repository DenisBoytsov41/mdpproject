import re
import datetime
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from schedule_processing import process_schedule_response
from utils import NoVerifyHTTPAdapter, save_response_to_file, save_request_to_file
import asyncio
import time
from APIelements.ButtonManager import ButtonPaginator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from config import *

input_lock = asyncio.Lock()
input_history = {}
update_queue = asyncio.Queue()

def get_unique_message_id():
    return int(time.time())

async def send_telegram_message(bot, chat_id, messages):
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(chat_id, text=message_text[i:i+max_message_length])

async def send_telegram_message_with_keyboard(bot, chat_id, text, options, callback_variable_name):
    try:
        buttons_per_page = 15
        buttons_per_row = 5

        current_page = 1

        total_pages = (len(options) + buttons_per_page - 1) // buttons_per_page  # Рассчитываем общее количество страниц

        while True:
            start_index = (current_page - 1) * buttons_per_page
            end_index = min(current_page * buttons_per_page, len(options))

            keyboard_buttons = options[start_index:end_index]

            # Создаем кнопки для текущей страницы
            char = []
            row_buttons = []  # Создаем список для кнопок текущей строки
            for button in keyboard_buttons:
                row_buttons.append(button[0])
                if len(row_buttons) == buttons_per_row:  # Добавляем по buttons_per_row кнопок в каждую строку
                    char.append(row_buttons)
                    row_buttons = []  # Обнуляем список для следующей строки
            if row_buttons:  # Добавляем оставшиеся кнопки, если они есть
                char.append(row_buttons)

            # Добавляем кнопки для переключения страниц
            navigation_buttons = []
            if current_page > 1:
                navigation_buttons.append(InlineKeyboardButton("<< Предыдущая", callback_data=f"{callback_variable_name}_prev_{current_page}"))
            if current_page < total_pages:
                navigation_buttons.append(InlineKeyboardButton("Следующая >>", callback_data=f"{callback_variable_name}_next_{current_page}"))

            # Добавляем кнопки для переключения страниц в конец разметки
            if navigation_buttons:
                char.append(navigation_buttons)

            markup = InlineKeyboardMarkup(char)
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

            # Ждем колбэка от пользователя
            response = await update_queue.get()
            if response == f"{callback_variable_name}_prev_{current_page}" and current_page > 1:
                current_page -= 1
            elif response == f"{callback_variable_name}_next_{current_page}" and current_page < total_pages:
                current_page += 1
            else:
                break

    except Exception as e:
        print("Ошибка отправки:", e)

async def get_input(bot, update, user_id, prompt):
    await bot.send_message(chat_id=update.message.chat_id, text=prompt)

    while True:
        await asyncio.sleep(1)
        async with input_lock:
            updates = await bot.get_updates(offset=update.update_id + 1)
            if len(updates) != 0:
                update = updates[-1]
            if updates and int(user_id) == update.effective_user.id:
                last_input_time = input_history.get(update.effective_user.id, 0)
                new_updates = [u for u in updates if u.message.date.timestamp() > last_input_time]
                if new_updates:
                    response = new_updates[-1].message.text
                    if response is not None and not response.startswith('/'):
                        # Сохраняем содержимое ответа и время его получения
                        input_history[update.message.chat_id] = new_updates[-1].message.date.timestamp()
                        return response

async def select_schedule(bot, driver, update, user_id):
    select_element_semester = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "semester"))
    )

    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')
    select_element_semester = soup.find('select', {'id': 'semester'})

    if select_element_semester:
        options_semester = select_element_semester.find_all('option')

        buttons = []
        for i, option_semester in enumerate(options_semester[1:], start=1):
            button = InlineKeyboardButton(f"{i}. {option_semester.text}", callback_data=f"semester{i}")
            buttons.append([button])

        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="semester")
        await paginator.start(user_id, bot)
        selected_semester_index = await paginator.run()

        await bot.send_message(chat_id=user_id, text="Нажмите на кнопку:")
        sem_input_sent = False
        while selected_semester_index is None:
            if not sem_input_sent:
                await send_telegram_message(bot, user_id, ["Пожалуйста, введите номер семестра."])
                sem_input_sent = True
            user_input = paginator.button_pressed
            if paginator.update is not None:
                update = paginator.update
            if user_input is not None:
                try:
                    selected_semester_index = int(user_input)
                except ValueError:
                    await send_telegram_message(bot, user_id, ["Некорректный ввод. Введите число."])
            else:
                if update and update.callback_query and update.callback_query.data is not None:
                    if update.callback_query.data.split('_')[-1] == paginator.session_id:
                        await paginator.handle_callback_query(update.callback_query, update, bot)
                    else:
                        await asyncio.sleep(1)
        paginator.clear_state()

        semester_id_mapping = {
            1: 8,
            2: 4,
            3: 3,
            4: 2,
            5: 1
        }

        if selected_semester_index not in semester_id_mapping:
            await send_telegram_message(bot, update.message.chat_id, ["Недопустимый номер семестра."])
            return

        selected_semester_id = semester_id_mapping[selected_semester_index]

        # Создаем кнопки для выбора "student" или "teacher"
        user_type_buttons = []
        button1 = InlineKeyboardButton("Student", callback_data="usertype1")
        user_type_buttons.append([button1])
        button2 = InlineKeyboardButton("Teacher", callback_data="usertype2")
        user_type_buttons.append([button2])

        # Новый экземпляр ButtonPaginator для выбора типа пользователя
        user_type_paginator = ButtonPaginator(user_type_buttons, TELEGRAM_API_TOKEN, user_id, callback_command="usertype")

        await send_telegram_message(bot, user_id, ["Выберите 'student' для расписания студента или 'teacher' для расписания преподавателя:"])
        await user_type_paginator.start(user_id, bot)
        user_type_selected = await user_type_paginator.run()
        user_type_input_sent = False
        user_selected = None
        while user_type_selected is None:
            if not user_type_input_sent:
                await send_telegram_message(bot, user_id, ["Пожалуйста, выберите 'student' или 'teacher'."])
                user_type_input_sent = True
            user_type_selected = int(user_type_paginator.button_pressed)
            if user_type_paginator.update is not None:
                update = user_type_paginator.update
        if user_type_selected is not None:
            try:
                if user_type_selected == 1:
                    user_selected = "student"
                    print(user_selected)
                elif user_type_selected == 2:
                    user_selected = "teacher"
                    print(user_selected)
                else:
                    raise ValueError
            except ValueError:
                await send_telegram_message(bot, user_id, ["Некорректный ввод. Введите 'student' или 'teacher'."])
        else:
            if update and update.callback_query and update.callback_query.data is not None:
                callback_data = update.callback_query.data
                if isinstance(callback_data, str) and '_' in callback_data:
                    if callback_data.split('_')[-1] == user_type_paginator.session_id:
                        await user_type_paginator.handle_callback_query(update.callback_query, update, bot)
                    else:
                        await asyncio.sleep(1)
        if user_selected.lower() == 'student':
            data_request = {
                "request": "institute",
                "semester": selected_semester_id
            }

            try:
                response_request = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                 data=data_request)
                response_request.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_request.text)

            if not options_output:
                await send_telegram_message(bot, user_id, ["На странице нет институтов."])
                return

            buttons = []
            for i, (value, text) in enumerate(options_output, start=1):
                button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"institute{i}")
                buttons.append([button])

            paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="institute")
            await send_telegram_message(bot, user_id, ["Выберите институт:"])
            await paginator.start(user_id, bot)
            selected_institute_index = await paginator.run()

            if selected_institute_index is not None:
                selected_institute = options_output[selected_institute_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбран институт: {selected_institute}"])

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
                    await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                    return

                options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                            response_speciality.text)

                if not options_output:
                    await send_telegram_message(bot, user_id, ["На странице нет специальностей."])
                    return

                buttons = []
                for i, (value, text) in enumerate(options_output, start=1):
                    button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"speciality{i}")
                    buttons.append([button])

                paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="speciality")
                await send_telegram_message(bot, user_id, ["Выберите специальность:"])
                await paginator.start(user_id, bot)
                selected_speciality_index = await paginator.run()

                if selected_speciality_index is not None:
                    selected_speciality = options_output[selected_speciality_index - 1][1]
                    await send_telegram_message(bot, user_id, [f"Выбрана специальность: {selected_speciality}"])

                    # Далее запрос информации о группах
                    data_group = {
                        "request": "group",
                        "semester": selected_semester_id,
                        "institute": selected_institute,
                        "speciality": selected_speciality
                    }

                    try:
                        response_group = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_group)
                        response_group.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                        return

                    options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_group.text)

                    if not options_output:
                        await send_telegram_message(bot, user_id, ["На странице нет групп."])
                        return

                    # Создание кнопок для пагинации групп
                    buttons = []
                    for i, (value, text) in enumerate(options_output, start=1):
                        button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"group{i}")
                        buttons.append([button])
                    paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command='group')
                    await send_telegram_message(bot, user_id, ["Выберите группу:"])
                    await paginator.start(user_id, bot)
                    selected_group_index = await paginator.run()

                    if selected_group_index is not None:
                        selected_group = options_output[selected_group_index - 1][1]
                        await send_telegram_message(bot, user_id, [f"Выбрана группы: {selected_group}"])
                        data_schedule = {
                            "request": "stimetable",
                            "semester": selected_semester_id,
                            "institute": selected_institute,
                            "speciality": selected_speciality,
                            "group": selected_group
                        }

                        try:
                            response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)
                            response_schedule.raise_for_status()

                            # save_request_to_file(update, response_schedule.request)
                            # save_response_to_file(update, response_schedule)

                            return process_schedule_response(response_schedule, selected_semester_id,
                                                             institute=selected_institute,
                                                             speciality=selected_speciality,
                                                             group=selected_group)
                        except requests.exceptions.RequestException as e:
                            await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                            return
                else:
                    await send_telegram_message(bot, user_id, ["Вы не выбрали специальность."])
            else:
                await send_telegram_message(bot, user_id, ["Вы не выбрали институт."])

        elif user_selected.lower() == 'teacher':
            data_request = {
                "request": "teacher",
                "semester": selected_semester_id
            }

            try:
                response_request = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                 data=data_request)
                response_request.raise_for_status()
            except requests.exceptions.RequestException as e:
                await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                return

            options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>',
                                        response_request.text)

            if not options_output:
                await send_telegram_message(bot, user_id ["На странице нет преподавателей."])
                return

            buttons = []
            for i, (value, text) in enumerate(options_output, start=1):
                button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"teacher{i}")
                buttons.append([button])

            paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="teacher")
            await paginator.start(user_id, bot)
            selected_teacher_index = await paginator.run()

            if selected_teacher_index is not None:
                selected_teacher = options_output[selected_teacher_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбран преподаватель: {selected_teacher}"])

                data_schedule = {
                    "request": "ttimetable",
                    "semester": selected_semester_id,
                    "teacher": selected_teacher
                }

                try:
                    response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php",
                                                      data=data_schedule)
                    response_schedule.raise_for_status()

                    # save_request_to_file(update, response_schedule.request)
                    # save_response_to_file(update, response_schedule)

                    return process_schedule_response(response_schedule, selected_semester_id,
                                                     teacher=selected_teacher)
                except requests.exceptions.RequestException as e:
                    await send_telegram_message(bot, user_id, [f"Ошибка запроса: {e}"])
                    return

