import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from schedule_processing import process_schedule_response
import asyncio
from allClasses.ButtonManager import ButtonPaginator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_API_TOKEN
import collections
from telegram.ext import CallbackContext

# Словарь для хранения истории ввода пользователя
input_history = {}
# Словарь для хранения обработанных обновлений
processed_updates = {}
# Элемент для выбора семестра на веб-странице
select_element_semester = None
# Переменная для хранения расписания
schedule = None

# Метод для отправки сообщения в Telegram
async def send_telegram_message(bot, chat_id, messages):
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(chat_id, text=message_text[i:i + max_message_length])

# Метод для получения DOM-элемента на веб-странице
async def get_dom_element(bot, driver, update, user_id, element_id="semester", wait_time=10):
    try:
        global select_element_semester
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        select_element_semester = soup.find('select', {'id': element_id})
        if select_element_semester:
            return await select_semester(bot, driver, update, user_id, select_element_semester)
        else:
            await send_telegram_message(bot, user_id, ["Элемент не найден."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Ошибка при получении элемента DOM: {e}"])

# Метод для обработки выбора семестра
async def select_semester(bot, driver, update, user_id, select_element_semester):
    try:
        options_semester = select_element_semester.find_all('option')
        buttons = []
        for i, option_semester in enumerate(options_semester[1:], start=1):
            button = InlineKeyboardButton(f"{i}. {option_semester.text}", callback_data=f"semester{i}")
            buttons.append([button])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_semester")
        buttons.append([button])
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="semester")
        await paginator.start(user_id, bot)
        await bot.send_message(chat_id=user_id, text="Нажмите на кнопку:")
        selected_semester_index = await paginator.run(processed_updates)
        sem_input_sent = False
        await clear_all_callbacks(bot)
        update = paginator.update
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
        update = paginator.update
        if selected_semester_index not in semester_id_mapping:
            await send_telegram_message(bot, user_id, ["Возврат к предыдущему запросу не возможен. Выход из функции."])
            await asyncio.sleep(1)
            paginator.clear_state()
            return

        selected_semester_id = semester_id_mapping[selected_semester_index]
        if user_id not in input_history:
            input_history[user_id] = {}
        update = paginator.update
        if selected_semester_id is not None:
            input_history[user_id]["selected_semester"] = selected_semester_id
            return await select_user_type(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите семестр."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора типа пользователя (студент или преподаватель)
async def select_user_type(bot, driver, update, user_id):
    try:
        selected_semester_id = input_history[user_id]["selected_semester"]
        # Создаем кнопки для выбора "student" или "teacher"
        user_type_buttons = []
        button1 = InlineKeyboardButton("Student", callback_data="usertype1")
        user_type_buttons.append([button1])
        button2 = InlineKeyboardButton("Teacher", callback_data="usertype2")
        user_type_buttons.append([button2])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_usertype")
        user_type_buttons.append([button])

        # Новый экземпляр ButtonPaginator для выбора типа пользователя
        user_type_paginator = ButtonPaginator(user_type_buttons, TELEGRAM_API_TOKEN, user_id, callback_command="usertype")

        await send_telegram_message(bot, user_id, ["Выберите 'student' для расписания студента или 'teacher' для расписания преподавателя:"])
        await user_type_paginator.start(user_id, bot)
        user_type_selected = await user_type_paginator.run(processed_updates)
        update = user_type_paginator.update
        await clear_all_callbacks(bot)
        if user_type_selected is not None:
            if user_type_selected == 1:
                selected_user_type = "student"
            elif user_type_selected == 2:
                selected_user_type = "teacher"
            else:
                selected_user_type = "backrequest_usertype"
            input_history[user_id]["selected_usertype"] = selected_user_type
            update = user_type_paginator.update
            if selected_user_type == "student":
                await send_telegram_message(bot, user_id, [f"Выбран тип пользователя: {selected_user_type}"])
                return await select_institute(bot, driver, update, user_id)
            elif selected_user_type == "teacher":
                await send_telegram_message(bot, user_id, [f"Выбран тип пользователя: {selected_user_type}"])
                return await select_teacher(bot, driver, update, user_id)
            elif selected_user_type == "backrequest_usertype":
                #await send_telegram_message(bot, user_id, ["Возврат к предыдущему запросу - Выбору семестра."])
                await handle_back_button(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите 'student' или 'teacher'."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора института
async def select_institute(bot, driver, update, user_id):
    try:
        # Получаем выбранный семестр из состояния пользователя
        selected_semester_id = input_history[user_id]["selected_semester"]

        data_request = {
            "request": "institute",
            "semester": selected_semester_id
        }

        response_request = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)
        response_request.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_request.text)

        if not options_output:
            await send_telegram_message(bot, user_id, ["На странице нет институтов."])
            return

        buttons = []
        for i, (value, text) in enumerate(options_output, start=1):
            button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"institute{i}")
            buttons.append([button])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_institute")
        buttons.append([button])
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="institute")
        await send_telegram_message(bot, user_id, ["Выберите институт:"])
        await paginator.start(user_id, bot)
        selected_institute_index = await paginator.run(processed_updates)
        update = paginator.update
        await clear_all_callbacks(bot)
        if selected_institute_index is not None:
            if str(selected_institute_index) == "backrequest_institute":
                input_history[user_id]["selected_institute"] = selected_institute_index
                await handle_back_button(bot, driver, update, user_id)
            else:
                selected_institute = options_output[selected_institute_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбран институт: {selected_institute}"])
                input_history[user_id]["selected_institute"] = selected_institute
                return await select_speciality(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите институт."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора специальности
async def select_speciality(bot, driver, update, user_id):
    try:
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]
        data_speciality = {
            "request": "speciality",
            "semester": selected_semester_id,
            "institute": selected_institute
        }

        response_speciality = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_speciality)
        response_speciality.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_speciality.text)

        if not options_output:
            await send_telegram_message(bot, user_id, ["На странице нет специальностей."])
            return

        buttons = []
        for i, (value, text) in enumerate(options_output, start=1):
            button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"speciality{i}")
            buttons.append([button])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_speciality")
        buttons.append([button])
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="speciality")
        await send_telegram_message(bot, user_id, ["Выберите специальность:"])
        await paginator.start(user_id, bot)
        selected_speciality_index = await paginator.run(processed_updates)
        update = paginator.update
        await clear_all_callbacks(bot)
        if selected_speciality_index is not None:
            if str(selected_speciality_index) == "backrequest_speciality":
                input_history[user_id]["selected_speciality"] = selected_speciality_index
                await handle_back_button(bot, driver, update, user_id)
            else:
                selected_speciality = options_output[selected_speciality_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбрана специальность: {selected_speciality}"])
                input_history[user_id]["selected_speciality"] = selected_speciality
                return await select_group(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите специальность."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора группы
async def select_group(bot, driver, update, user_id):
    try:
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]
        selected_speciality = input_history[user_id]["selected_speciality"]
        data_group = {
            "request": "group",
            "semester": selected_semester_id,
            "institute": selected_institute,
            "speciality": selected_speciality
        }

        response_group = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_group)
        response_group.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_group.text)

        if not options_output:
            await send_telegram_message(bot, user_id, ["На странице нет групп."])
            return

        buttons = []
        for i, (value, text) in enumerate(options_output, start=1):
            button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"group{i}")
            buttons.append([button])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_group")
        buttons.append([button])
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="group")
        await send_telegram_message(bot, user_id, ["Выберите группу:"])
        await paginator.start(user_id, bot)
        selected_group_index = await paginator.run(processed_updates)
        update = paginator.update
        await clear_all_callbacks(bot)
        if selected_group_index is not None:
            if str(selected_group_index) == "backrequest_group":
                input_history[user_id]["selected_group"] = selected_group_index
                await handle_back_button(bot, driver, update, user_id)
            else:
                selected_group = options_output[selected_group_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбрана группы: {selected_group}"])
                input_history[user_id]["selected_group"] = selected_group

            # После выбора группы, мы можем вызвать функцию для получения расписания
            return await get_schedule(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите группу."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для получения расписания
async def get_schedule(bot, driver, update, user_id):
    try:
        global schedule
        # Получаем информацию о выборах пользователя из истории
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]
        selected_speciality = input_history[user_id]["selected_speciality"]
        selected_group = input_history[user_id]["selected_group"]

        data_schedule = {
            "request": "stimetable",
            "semester": selected_semester_id,
            "institute": selected_institute,
            "speciality": selected_speciality,
            "group": selected_group
        }

        response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)
        response_schedule.raise_for_status()

        # Обработка полученного расписания
        schedule = process_schedule_response(response_schedule, selected_semester_id,
                                             institute=selected_institute,
                                             speciality=selected_speciality,
                                             group=selected_group)

        return schedule
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора преподавателя
async def select_teacher(bot, driver, update, user_id):
    try:
        selected_semester_id = input_history[user_id]["selected_semester"]
        data_request = {
            "request": "teacher",
            "semester": selected_semester_id
        }

        response_request = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)
        response_request.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_request.text)

        if not options_output:
            await send_telegram_message(bot, user_id, ["На странице нет преподавателей."])
            return

        buttons = []
        for i, (value, text) in enumerate(options_output, start=1):
            button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"teacher{i}")
            buttons.append([button])
        button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_teacher")
        buttons.append([button])
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="teacher")
        await paginator.start(user_id, bot)
        selected_teacher_index = await paginator.run(processed_updates)
        update = paginator.update
        await clear_all_callbacks(bot)
        if selected_teacher_index is not None:
            if str(selected_teacher_index) == "backrequest_teacher":
                input_history[user_id]["selected_speciality"] = selected_teacher_index
                await handle_back_button(bot, driver, update, user_id)
            else:
                selected_teacher = options_output[selected_teacher_index - 1][1]
                await send_telegram_message(bot, user_id, [f"Выбран преподаватель: {selected_teacher}"])
                input_history[user_id]["selected_teacher"] = selected_teacher
                # После выбора преподавателя, мы можем вызвать функцию для получения расписания
                return await get_teacher_schedule(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите преподавателя."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для получения расписания преподавателя
async def get_teacher_schedule(bot, driver, update, user_id):
    try:
        global schedule
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_teacher = input_history[user_id]["selected_teacher"]
        data_schedule = {
            "request": "ttimetable",
            "semester": selected_semester_id,
            "teacher": selected_teacher
        }

        response_schedule = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)
        response_schedule.raise_for_status()

        # Обработка полученного расписания
        schedule = process_schedule_response(response_schedule, selected_semester_id,
                                             teacher=selected_teacher)
        return schedule
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки нажатия на кнопку "Назад"
async def handle_back_button(bot, driver, update, user_id):
    try:
        # Проверяем, есть ли какие-либо предыдущие выборы в истории пользователя
        if user_id in input_history and input_history[user_id]:
            # Удаляем последний выбор из истории
            input_history[user_id].popitem()
            # Перенаправляем пользователя на предыдущий этап
            return await navigate_to_previous_stage(bot, driver, update, user_id)
        else:
            # Если история пользователя пуста, отправляем сообщение об ошибке
            await send_telegram_message(bot, user_id, ["Нет предыдущих этапов для возврата."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для навигации к предыдущему этапу выбора
async def navigate_to_previous_stage(bot, driver, update, user_id):
    try:
        global select_element_semester
        await clear_all_callbacks(bot)
        # Проверяем, есть ли какие-либо предыдущие выборы в истории пользователя
        if user_id in input_history and input_history[user_id]:
            # Получаем последний выбор пользователя из истории
            last_choice = input_history[user_id]
            if len(last_choice) >=1:
                last_choice = collections.deque(last_choice,maxlen=1)[0]
            else:
                last_choice = None
            # Определяем тип этапа и перенаправляем пользователя соответственно
            if last_choice == "selected_semester":
                input_history[user_id].popitem()
                await select_semester(bot, driver, update, user_id, select_element_semester)
            elif last_choice == "selected_usertype":
                input_history[user_id].popitem()
                await select_user_type(bot, driver, update, user_id)
            elif last_choice == "selected_institute":
                input_history[user_id].popitem()
                await select_institute(bot, driver, update, user_id)
            elif last_choice == "selected_speciality":
                input_history[user_id].popitem()
                await select_speciality(bot, driver, update, user_id)
            elif last_choice == "selected_group":
                input_history[user_id].popitem()
                await select_group(bot, driver, update, user_id)
            elif last_choice == "selected_teacher":
                input_history[user_id].popitem()
                await select_teacher(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Нет предыдущих этапов для возврата."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для очистки всех callback'ов
async def clear_all_callbacks(bot):
    try:
        updates = await bot.get_updates()

        for update in updates:
            if update.callback_query:
                update_id = update.callback_query.message.message_id
                if update_id not in processed_updates:
                    processed_updates[update_id] = update_id
            if update.message:
                update_id = update.message.message_id
                if update_id not in processed_updates:
                    processed_updates[update_id] = update_id

    except Exception as e:
        print(f"Ошибка при очистке callback'ов: {e}")

# Метод для возврата расписания
async def back_schedule(bot, driver, update, user_id):
    try:
        global schedule
        while schedule is None:
            await asyncio.sleep(0.1)
        return schedule
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Ошибка: {e}"])

