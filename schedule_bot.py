import os
import json
import asyncio
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import *

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_list = [
        "/createCal - Создать календарь расписания, который добавится выбранному пользователю",
    ]
    await update.message.reply_text("Доступные команды:\n" + "\n".join(command_list))
    await log_message(update)

async def start_JSON(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await log_message(update)
        update_json = update.to_dict()
        update_json_str = json.dumps(update_json)
        # Запускаем корутин в фоновом режиме для обработки запроса
        asyncio.create_task(handle_create_cal(update, update_json_str))
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}")

async def send_telegram_message(update: Update, message: str):
    await update.message.reply_text(message)

async def log_message(update: Update):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    message = update.message.text

    with open("bot.log", "a") as log_file:
        log_file.write(f"User ID: {user_id}\n")
        log_file.write(f"Username: {username}\n")
        log_file.write(f"Message: {message}\n\n")

async def handle_create_cal(update: Update, update_json_str: str):
    try:
        subprocess.run([PYTHON_EXE, START_CREATE_JSON_SCRIPT, update_json_str, TELEGRAM_API_TOKEN, str(update.effective_user.id)], check=True)
    except Exception as e:
        await send_telegram_message(update, f"Ошибка: {e}")

if TELEGRAM_API_TOKEN is None:
    print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
    exit(1)

app = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

app.handlers.clear()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("createCal", start_JSON))

app.run_polling()
