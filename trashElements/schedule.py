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
    """
        Отправляет сообщения пользователю в Telegram.

        Args:
            bot: Объект бота Telegram.
            chat_id: ID чата, куда отправляется сообщение.
            messages: Список сообщений для отправки.

        Returns:
            None
        """
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(chat_id, text=message_text[i:i + max_message_length])

# Метод для получения DOM-элемента на веб-странице
async def get_dom_element(bot, driver, update, user_id, element_id="semester", wait_time=10):
    """
       Получает DOM-элемент на веб-странице.

       Args:
           bot: Объект бота Telegram.
           driver: Веб-драйвер для работы с веб-страницами.
           update: Объект обновления Telegram.
           user_id: ID пользователя.
           element_id: ID DOM-элемента для поиска.
           wait_time: Время ожидания появления элемента.

       Returns:
           None
       """
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
async def display_semester_options(bot, user_id, select_element_semester):
    """
    Отображает варианты семестра и запускает пагинатор для выбора.
    """
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

        return paginator
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка при отображении вариантов семестра: {e}"])
        return None


async def handle_semester_selection(bot, driver, update, user_id, paginator):
    """
    Обрабатывает выбор семестра, обновляет историю ввода и вызывает следующий этап.
    """
    try:
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

# Метод для выбора семестра
async def select_semester(bot, driver, update, user_id, select_element_semester):
    """
    Основная функция для выбора семестра, которая вызывает вспомогательные методы.
    """
    paginator = await display_semester_options(bot, user_id, select_element_semester)
    if paginator:
        await handle_semester_selection(bot, driver, update, user_id, paginator)

async def display_user_type_options(bot, user_id):
    """
    Отображает варианты выбора типа пользователя и запускает пагинатор.
    """
    try:
        # Создаем кнопки для выбора "student" или "teacher"
        user_type_buttons = [
            [InlineKeyboardButton("Student", callback_data="usertype1")],
            [InlineKeyboardButton("Teacher", callback_data="usertype2")],
            [InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_usertype")]
        ]

        # Новый экземпляр ButtonPaginator для выбора типа пользователя
        user_type_paginator = ButtonPaginator(user_type_buttons, TELEGRAM_API_TOKEN, user_id,
                                              callback_command="usertype")

        await send_telegram_message(bot, user_id, [
            "Выберите 'student' для расписания студента или 'teacher' для расписания преподавателя:"])
        await user_type_paginator.start(user_id, bot)

        return user_type_paginator
    except Exception as e:
        await send_telegram_message(bot, user_id,
                                    [f"Произошла ошибка при отображении вариантов типа пользователя: {e}"])
        return None

async def handle_user_type_selection(bot, driver, update, user_id, paginator):
    """
    Обрабатывает выбор типа пользователя, обновляет историю ввода и вызывает соответствующий этап.
    """
    try:
        user_type_selected = await paginator.run(processed_updates)
        await clear_all_callbacks(bot)
        update = paginator.update

        if user_type_selected is not None:
            if user_type_selected == 1:
                selected_user_type = "student"
            elif user_type_selected == 2:
                selected_user_type = "teacher"
            else:
                selected_user_type = "backrequest_usertype"

            input_history[user_id]["selected_usertype"] = selected_user_type
            update = paginator.update

            if selected_user_type == "student":
                await send_telegram_message(bot, user_id, [f"Выбран тип пользователя: {selected_user_type}"])
                return await select_institute(bot, driver, update, user_id)
            elif selected_user_type == "teacher":
                await send_telegram_message(bot, user_id, [f"Выбран тип пользователя: {selected_user_type}"])
                return await select_teacher(bot, driver, update, user_id)
            elif selected_user_type == "backrequest_usertype":
                await handle_back_button(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите 'student' или 'teacher'."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора типа пользователя (студент или преподаватель)
async def select_user_type(bot, driver, update, user_id):
    """
    Основная функция для выбора типа пользователя, которая вызывает вспомогательные методы.
    """
    selected_semester_id = input_history[user_id]["selected_semester"]
    paginator = await display_user_type_options(bot, user_id)
    if paginator:
        await handle_user_type_selection(bot, driver, update, user_id, paginator)

async def fetch_institutes(selected_semester_id):
    """
    Делает запрос к серверу и получает список институтов для выбранного семестра.

    :param selected_semester_id: Идентификатор выбранного семестра
    :return: Список кортежей (значение, текст) для каждого института или None в случае ошибки
    """
    try:
        data_request = {
            "request": "institute",
            "semester": selected_semester_id
        }

        response = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)
        response.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response.text)

        return options_output if options_output else None
    except requests.RequestException as e:
        print(f"Ошибка при запросе институтов: {e}")
        return None

async def handle_institute_selection(bot, driver, update, user_id, options_output):
    """
    Отображает варианты институтов, запускает пагинатор и обрабатывает выбор.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    :param options_output: Список кортежей (значение, текст) для каждого института
    """
    try:
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

# Метод для обработки выбора института
async def select_institute(bot, driver, update, user_id):
    """
    Основная функция для выбора института, которая вызывает вспомогательные методы.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    """
    try:
        # Получаем выбранный семестр из состояния пользователя
        selected_semester_id = input_history[user_id]["selected_semester"]

        options_output = await fetch_institutes(selected_semester_id)

        if options_output:
            await handle_institute_selection(bot, driver, update, user_id, options_output)
        else:
            await send_telegram_message(bot, user_id, ["На странице нет институтов."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

async def fetch_specialities(selected_semester_id, selected_institute):
    """
    Делает запрос к серверу и получает список специальностей для выбранного семестра и института.

    :param selected_semester_id: Идентификатор выбранного семестра
    :param selected_institute: Идентификатор выбранного института
    :return: Список кортежей (значение, текст) для каждой специальности или None в случае ошибки
    """
    try:
        data_speciality = {
            "request": "speciality",
            "semester": selected_semester_id,
            "institute": selected_institute
        }

        response = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_speciality)
        response.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response.text)

        return options_output if options_output else None
    except requests.RequestException as e:
        print(f"Ошибка при запросе специальностей: {e}")
        return None

async def handle_speciality_selection(bot, driver, update, user_id, options_output):
    """
    Отображает варианты специальностей, запускает пагинатор и обрабатывает выбор.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    :param options_output: Список кортежей (значение, текст) для каждой специальности
    """
    try:
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

# Метод для обработки выбора специальности
async def select_speciality(bot, driver, update, user_id):
    """
    Основная функция для выбора специальности, которая вызывает вспомогательные методы.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    """
    try:
        # Получаем выбранный семестр и институт из состояния пользователя
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]

        options_output = await fetch_specialities(selected_semester_id, selected_institute)

        if options_output:
            await handle_speciality_selection(bot, driver, update, user_id, options_output)
        else:
            await send_telegram_message(bot, user_id, ["На странице нет специальностей."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

async def fetch_groups(selected_semester_id, selected_institute, selected_speciality):
    """
    Делает запрос к серверу и получает список групп для выбранного семестра, института и специальности.

    :param selected_semester_id: Идентификатор выбранного семестра
    :param selected_institute: Идентификатор выбранного института
    :param selected_speciality: Идентификатор выбранной специальности
    :return: Список кортежей (значение, текст) для каждой группы или None в случае ошибки
    """
    try:
        data_group = {
            "request": "group",
            "semester": selected_semester_id,
            "institute": selected_institute,
            "speciality": selected_speciality
        }

        response = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_group)
        response.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response.text)

        return options_output if options_output else None
    except requests.RequestException as e:
        print(f"Ошибка при запросе групп: {e}")
        return None

async def handle_group_selection(bot, driver, update, user_id, options_output):
    """
    Отображает варианты групп, запускает пагинатор и обрабатывает выбор.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    :param options_output: Список кортежей (значение, текст) для каждой группы
    """
    try:
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
                await send_telegram_message(bot, user_id, [f"Выбрана группа: {selected_group}"])
                input_history[user_id]["selected_group"] = selected_group

            # После выбора группы, вызываем функцию для получения расписания
            return await get_schedule(bot, driver, update, user_id)
        else:
            await send_telegram_message(bot, user_id, ["Пожалуйста, выберите группу."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для обработки выбора группы
async def select_group(bot, driver, update, user_id):
    """
    Основная функция для выбора группы, которая вызывает вспомогательные методы.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    """
    try:
        # Получаем выбранный семестр, институт и специальность из состояния пользователя
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]
        selected_speciality = input_history[user_id]["selected_speciality"]

        options_output = await fetch_groups(selected_semester_id, selected_institute, selected_speciality)

        if options_output:
            await handle_group_selection(bot, driver, update, user_id, options_output)
        else:
            await send_telegram_message(bot, user_id, ["На странице нет групп."])
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

async def fetch_schedule(selected_semester_id, selected_institute, selected_speciality, selected_group):
    """
    Делает запрос к серверу и получает расписание для выбранного семестра, института, специальности и группы.

    :param selected_semester_id: Идентификатор выбранного семестра
    :param selected_institute: Идентификатор выбранного института
    :param selected_speciality: Идентификатор выбранной специальности
    :param selected_group: Идентификатор выбранной группы
    :return: Ответ сервера с расписанием или None в случае ошибки
    """
    try:
        data_schedule = {
            "request": "stimetable",
            "semester": selected_semester_id,
            "institute": selected_institute,
            "speciality": selected_speciality,
            "group": selected_group
        }

        response = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_schedule)
        response.raise_for_status()

        return response
    except requests.RequestException as e:
        print(f"Ошибка при запросе расписания: {e}")
        return None

# Метод для получения расписания
async def get_schedule(bot, driver, update, user_id):
    try:
        """
            Основная функция для получения расписания, которая вызывает вспомогательные методы.

            :param bot: Объект Bot
            :param driver: Объект WebDriver
            :param update: Объект Update
            :param user_id: Идентификатор пользователя
            """
        global schedule
        # Получаем информацию о выборах пользователя из истории
        selected_semester_id = input_history[user_id]["selected_semester"]
        selected_institute = input_history[user_id]["selected_institute"]
        selected_speciality = input_history[user_id]["selected_speciality"]
        selected_group = input_history[user_id]["selected_group"]

        # Получаем расписание с сервера
        response_schedule = await fetch_schedule(selected_semester_id, selected_institute, selected_speciality, selected_group)

        if response_schedule:
            # Обрабатываем полученное расписание
            schedule = process_schedule_response(response_schedule, selected_semester_id,
                                                 institute=selected_institute,
                                                 speciality=selected_speciality,
                                                 group=selected_group)
            return schedule
        else:
            await send_telegram_message(bot, user_id, "Не удалось получить расписание.")
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

async def fetch_teacher_list(selected_semester_id):
    """
    Делает запрос к серверу и получает список преподавателей для выбранного семестра.

    :param selected_semester_id: Идентификатор выбранного семестра
    :return: Пары (значение, текст) для каждого преподавателя или None в случае ошибки
    """
    try:
        data_request = {
            "request": "teacher",
            "semester": selected_semester_id
        }

        response_request = requests.post("https://timetable.ksu.edu.ru/engine.php", data=data_request)
        response_request.raise_for_status()

        options_output = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response_request.text)
        return options_output
    except requests.RequestException as e:
        print(f"Ошибка при запросе списка преподавателей: {e}")
        return None

def create_teacher_buttons(options_output):
    """
    Создает кнопки для списка преподавателей.

    :param options_output: Список пар (значение, текст) для каждого преподавателя
    :return: Список кнопок для выбора преподавателя
    """
    buttons = []
    for i, (value, text) in enumerate(options_output, start=1):
        button = InlineKeyboardButton(f"{i}. {text}", callback_data=f"teacher{i}")
        buttons.append([button])
    button = InlineKeyboardButton("Назад к предыдущему запросу", callback_data="backrequest_teacher")
    buttons.append([button])
    return buttons

async def process_teacher_selection(bot, paginator, options_output, update, user_id, driver):
    """
    Обрабатывает выбор преподавателя пользователем.

    :param bot: Объект Bot
    :param paginator: Объект ButtonPaginator для управления кнопками
    :param options_output: Список пар (значение, текст) для каждого преподавателя
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    :param driver: Объект WebDriver
    """
    selected_teacher_index = await paginator.run(processed_updates)
    update = paginator.update
    await clear_all_callbacks(bot)
    if selected_teacher_index is not None:
        if str(selected_teacher_index) == "backrequest_teacher":
            input_history[user_id]["selected_teacher"] = selected_teacher_index
            await handle_back_button(bot, driver, update, user_id)
        else:
            selected_teacher = options_output[selected_teacher_index - 1][1]
            await send_telegram_message(bot, user_id, [f"Выбран преподаватель: {selected_teacher}"])
            input_history[user_id]["selected_teacher"] = selected_teacher
            # После выбора преподавателя, мы можем вызвать функцию для получения расписания
            return await get_teacher_schedule(bot, driver, update, user_id)
    else:
        await send_telegram_message(bot, user_id, ["Пожалуйста, выберите преподавателя."])

# Метод для обработки выбора преподавателя
async def select_teacher(bot, driver, update, user_id):
    """
    Основная функция для выбора преподавателя, которая вызывает вспомогательные методы.

    :param bot: Объект Bot
    :param driver: Объект WebDriver
    :param update: Объект Update
    :param user_id: Идентификатор пользователя
    """
    try:
        selected_semester_id = input_history[user_id]["selected_semester"]

        # Получаем список преподавателей с сервера
        options_output = await fetch_teacher_list(selected_semester_id)

        if not options_output:
            await send_telegram_message(bot, user_id, ["На странице нет преподавателей."])
            return

        # Создаем кнопки для выбора преподавателя
        buttons = create_teacher_buttons(options_output)
        paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, user_id, callback_command="teacher")

        await paginator.start(user_id, bot)
        await process_teacher_selection(bot, paginator, options_output, update, user_id, driver)
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Произошла ошибка: {e}"])

# Метод для получения расписания преподавателя
async def get_teacher_schedule(bot, driver, update, user_id):
    """
       Получает и обрабатывает расписание выбранного преподавателя.

       :param bot: Объект Bot
       :param driver: Объект WebDriver
       :param update: Объект Update
       :param user_id: Идентификатор пользователя
       :return: Расписание преподавателя или None в случае ошибки
       """
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
    """
        Обрабатывает нажатие кнопки "Назад", перенаправляя пользователя на предыдущий этап выбора.

        Args:
            bot: Объект бота Telegram.
            driver: Веб-драйвер для работы с веб-страницами.
            update: Объект обновления Telegram.
            user_id: ID пользователя.

        Returns:
            None
        """
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
    """
        Навигирует пользователя на предыдущий этап выбора.

        Args:
            bot: Объект бота Telegram.
            driver: Веб-драйвер для работы с веб-страницами.
            update: Объект обновления Telegram.
            user_id: ID пользователя.

        Returns:
            None
        """
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
    """
        Очищает все callback'и.

        Args:
            bot: Объект бота Telegram.

        Returns:
            None
        """
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
    """
       Возвращает расписание пользователя.

       Args:
           bot: Объект бота Telegram.
           driver: Веб-драйвер для работы с веб-страницами.
           update: Объект обновления Telegram.
           user_id: ID пользователя.

       Returns:
           schedule: Расписание пользователя.
       """
    try:
        global schedule
        while schedule is None:
            await asyncio.sleep(0.1)
        return schedule
    except Exception as e:
        await send_telegram_message(bot, user_id, [f"Ошибка: {e}"])

