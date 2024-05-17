import os
import json
import asyncio
import subprocess
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from config import *

user_button_state = {}

async def start(update: Update, bot: Bot):
    command_list = [
        "/createCal - Создать календарь расписания, который добавится выбранному пользователю",
    ]
    await bot.send_message(chat_id=update.message.chat_id, text="Доступные команды:\n" + "\n".join(command_list))
    await log_message(update)

async def start_JSON(update: Update, bot: Bot):
    try:
        await log_message(update)
        update_json = update.to_dict()
        update_json_str = json.dumps(update_json)
        keyboard = [[InlineKeyboardButton("Создать календарь", callback_data='create_cal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=update.message.chat_id, text="Выберите действие:", reply_markup=reply_markup)
        # Устанавливаем состояние кнопки для пользователя
        user_button_state.setdefault(update.message.from_user.id, {})['create_cal'] = False
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}", bot)

async def send_telegram_message(update: Update, message: str, bot: Bot):
    await bot.send_message(chat_id=update.message.chat_id, text=message)

async def send_telegram_message_2(chat_id, message: str, bot: Bot):
    await bot.send_message(chat_id=chat_id, text=message)

async def log_message(update: Update):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    message = update.message.text

    with open("bot.log", "a") as log_file:
        log_file.write(f"User ID: {user_id}\n")
        log_file.write(f"Username: {username}\n")
        log_file.write(f"Message: {message}\n\n")

async def handle_button_press(update: Update, bot: Bot):
    query = update.callback_query
    user_id = query.from_user.id
    button_id = query.data
    if user_button_state.get(user_id, {}).get(button_id, False):
        await send_telegram_message_2(query.message.chat.id, "Вы уже выбрали создание календаря", bot)
        try:
            await query.answer(cache_time=30)
        except BadRequest as e:
            print(f"Ошибка ответа на запрос обратного вызова: {e}")
        return  # Если кнопка уже была нажата, выходим из функции
    if button_id == 'create_cal':
        # Отправляем сообщение только если кнопка не была нажата ранее
        await send_telegram_message_2(query.message.chat.id, "Вы выбрали создание календаря", bot)
        user_button_state.setdefault(user_id, {})[button_id] = True
        update_json = update.to_dict()
        update_json_str = json.dumps(update_json)
        # Запускаем корутину в фоновом режиме для обработки запроса
        await asyncio.create_task(handle_create_cal(update, update_json_str, bot))
        # Устанавливаем время кэширования ответа на колбэк в 1 секунду
        try:
            await query.answer(cache_time=30)
        except BadRequest as e:
            print(f"Ошибка ответа на запрос обратного вызова: {e}")

async def handle_create_cal(update: Update, update_json_str: str, bot: Bot):
    try:
        subprocess.run([PYTHON_EXE, START_CREATE_JSON_SCRIPT, update_json_str, TELEGRAM_API_TOKEN, str(update.effective_user.id)], check=True)
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}", bot)
    finally:
        # Сбрасываем состояние кнопки после выполнения действия
        user_button_state.setdefault(update.effective_user.id, {})['create_cal'] = False

async def command_handler(update: Update, bot: Bot, offset_dict: dict):
    current_time = time.time()
    print("Получено обновление:", update.message.text)
    if update.message.text.startswith('/start'):
        print("Получена команда /start")
        if offset_dict.get(update.message.chat_id) != update.update_id:
            await start(update, bot)
            offset_dict[update.message.chat_id] = update.update_id
    elif update.message.text.startswith('/createCal'):
        print("Получена команда /createCal")
        last_command_update_id = offset_dict.get(update.message.chat_id, 0)
        if update.update_id != last_command_update_id:
            await start_JSON(update, bot)
            offset_dict[update.message.chat_id] = update.update_id
            # Обнуляем состояние кнопки при вызове команды /createCal
            user_button_state.pop(update.message.from_user.id, None)
        else:
            await send_telegram_message(update, "Пожалуйста, подождите 10 секунд перед отправкой следующей команды", bot)
    else:
        print("Неизвестная команда")
        await send_telegram_message(update, "Неизвестная команда", bot)

async def main():
    bot = Bot(token=TELEGRAM_API_TOKEN)
    await bot.initialize()
    offset_dict = {}
    max_update_id = 0
    while True:
        updates = await bot.get_updates(offset=max_update_id + 1, timeout=60)
        for update in updates:
            if update.message:
                await asyncio.create_task(command_handler(update, bot, offset_dict))
                max_update_id = update.update_id
            elif update.callback_query:
                await asyncio.create_task(handle_button_press(update, bot))
                # Устанавливаем максимальный ID для обработанных callback_query
                max_update_id = update.update_id
        await asyncio.sleep(1)


if TELEGRAM_API_TOKEN is None:
    print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
    exit(1)

asyncio.run(main())
