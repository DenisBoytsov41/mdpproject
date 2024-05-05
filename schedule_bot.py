import os
import json
import asyncio
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import *

async def send_telegram_message(update: Update, message: str):
    await update.message.reply_text(message)

async def get_telegram_input(update: Update, prompt: str):
    await update.message.reply_text(prompt)
    response = await asyncio.wait_for(app.wait_message(update.chat.id), timeout=None)
    return response.text

def start_JSON(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        update_json = update.to_dict()
        update_json_str = json.dumps(update_json)
        subprocess.run([PYTHON_EXE, START_CREATE_JSON_SCRIPT, update_json_str, TELEGRAM_API_TOKEN], check=True)
    except Exception as e:
        asyncio.run(send_telegram_message(update, f"Ошибка: {e}"))

if TELEGRAM_API_TOKEN is None:
    print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
    exit(1)

# Создаем экземпляр бота
app = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

app.handlers.clear()

app.add_handler(CommandHandler("startJSON", start_JSON))

app.run_polling()
