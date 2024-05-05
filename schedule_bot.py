import os
import json
import subprocess
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import *

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Привет, {update.effective_user.first_name}!')

async def run_python_script(script_path, input_file, output_file, update):
    try:
        process = await asyncio.create_subprocess_exec(
            PYTHON_EXE, script_path, input_file,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False  # Устанавливаем значение text в False
        )
        async for line in process.stdout:
            await send_output_to_bot(update, line.decode().strip())  # Декодируем байты в строку и отправляем результат в бота
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении скрипта: {e}")
    else:
        print("Скрипт успешно выполнен.")

async def send_output_to_bot(update: Update, message):
    await update.message.reply_text(message)

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получаем ввод пользователя
    user_input = update.message.text
    # Отправляем введенные данные в консоль
    print("Пользователь ввел в бота:", user_input)
    # Вызываем ваш скрипт с полученным вводом
    await schedule(update, context)

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    input_data = "user_input.txt"
    output_data = "output.txt"
    parameters = context.args
    # Проверяем, есть ли параметры для записи в файл
    if parameters:
        with open(input_data, "w") as f:
            f.write(" ".join(map(str, parameters)))  # Преобразуем параметры в строки перед объединением
        await run_python_script(START_CREATE_JSON_SCRIPT, input_data, output_data, update)
    else:
        # Если нет параметров, записываем в файл пустую строку
        with open(input_data, "w") as f:
            f.write("")
        await run_python_script(START_CREATE_JSON_SCRIPT, input_data, output_data, update)


if TELEGRAM_API_TOKEN is None:
    print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
    exit(1)

app = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))  # Обработчик для текстовых сообщений пользователя

app.run_polling()
