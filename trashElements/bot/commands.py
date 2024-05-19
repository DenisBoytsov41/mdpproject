import os
import json
import asyncio
import subprocess
from telegram import Bot, Update
from telegram.ext import CommandHandler, filters
from config import *

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
        await handle_create_cal(update, update_json_str, bot)
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}", bot)

async def send_telegram_message(update: Update, message: str, bot: Bot):
    await bot.send_message(chat_id=update.message.chat_id, text=message)

async def log_message(update: Update):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    message = update.message.text

    with open("bot.log", "a") as log_file:
        log_file.write(f"User ID: {user_id}\n")
        log_file.write(f"Username: {username}\n")
        log_file.write(f"Message: {message}\n\n")

async def handle_create_cal(update: Update, update_json_str: str, bot: Bot):
    try:
        subprocess.run([PYTHON_EXE, START_CREATE_JSON_SCRIPT, update_json_str, TELEGRAM_API_TOKEN, str(update.effective_user.id)], check=True)
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}", bot)

async def handle_commands(update, bot):
    print("Received message:", update.message.text)  # Добавляем отладочный вывод
    if update.message.text.startswith('/start'):
        await start(update, bot)
    elif update.message.text.startswith('/createCal'):
        await start_JSON(update, bot)
    else:
        await send_telegram_message(update, "Неизвестная команда", bot)

