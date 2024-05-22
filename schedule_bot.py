import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from config import *
from db.db_operations import *
from allClasses.TelegramBot import TelegramBot

# Отправляет пользователю список доступных команд
async def start(update: Update, bot: TelegramBot):
    """
        Отправляет пользователю список доступных команд бота.

        Args:
            update (Update): Обновление из Telegram.
            bot (TelegramBot): Экземпляр бота.
        """
    command_list = [f"/{cmd} - {desc}" for cmd, (desc, _) in bot.commands.items()]
    await bot.bot.send_message(chat_id=update.message.chat_id, text="Доступные команды:\n" + "\n".join(command_list))
    await log_message(update)

# Начинает процесс создания календаря и предлагает пользователю выбрать действие
async def start_JSON(update: Update, bot: TelegramBot):
    """
        Начинает процесс создания календаря и предлагает пользователю выбрать действие.

        Args:
            update (Update): Обновление из Telegram.
            bot (TelegramBot): Экземпляр бота.
        """
    try:
        await log_message(update)
        update_json = update.to_dict()
        update_json_str = json.dumps(update_json)
        keyboard = [[InlineKeyboardButton("Создать календарь", callback_data='create_cal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.bot.send_message(chat_id=update.message.chat_id, text="Выберите действие:", reply_markup=reply_markup)
        bot.user_button_state.setdefault(update.message.from_user.id, {})['create_cal'] = False
    except Exception as e:
        await bot.send_telegram_message(update, f"Ошибка: {e}")

# Логирует сообщение пользователя в файл
async def log_message(update: Update):
    """
        Логирует сообщение пользователя в файл.

        Args:
            update (Update): Обновление из Telegram.
        """
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    message = update.message.text

    with open("bot.log", "a") as log_file:
        log_file.write(f"User ID: {user_id}\n")
        log_file.write(f"Username: {username}\n")
        log_file.write(f"Message: {message}\n\n")

# Отправляет пользователю список доступных файлов .ics.
async def list_ics_files(update: Update, bot: TelegramBot):
    """
        Отправляет пользователю список доступных файлов .ics.

        Args:
            update (Update): Обновление из Telegram.
            bot (TelegramBot): Экземпляр бота.
        """
    user_id = update.effective_user.id
    try:
        ics_files = get_user_ics_files(user_id)
        if ics_files:
            files_list = "\n".join(ics_files)
            message = f"Доступные файлы .ics для пользователя {user_id}:\n{files_list}"
        else:
            message = f"Нет доступных файлов .ics для пользователя {user_id}."
        await bot.send_telegram_message(update, message)
    except Exception as e:
        await bot.send_telegram_message(update, f"Ошибка: {e}")

#Отправляет пользователю список доступных файлов .ics с кнопками для скачивания.
async def list_ics_files_down(update: Update, bot: TelegramBot):
    """
        Отправляет пользователю список доступных файлов .ics с кнопками для скачивания.

        Args:
            update (Update): Обновление из Telegram.
            bot (TelegramBot): Экземпляр бота.
        """
    user_id = update.effective_user.id
    try:
        ics_files = get_user_ics_files(user_id)
        if ics_files:
            buttons = []
            for file in ics_files:
                parts = file.split('__')
                if len(parts) >= 3:
                    identifier = f"{parts[0].split('_')[1]}_{parts[2]}"
                else:
                    identifier = file

                callback_data = f"download_{identifier}"
                button = InlineKeyboardButton(text=identifier, callback_data=callback_data)
                buttons.append([button])

            reply_markup = InlineKeyboardMarkup(buttons)
            await bot.bot.send_message(chat_id=update.message.chat_id,
                                   text=f"Доступные файлы .ics для пользователя {user_id}:", reply_markup=reply_markup)
        else:
            message = f"Нет доступных файлов .ics для пользователя {user_id}."
            await bot.send_telegram_message(update, message)
    except Exception as e:
        await bot.send_telegram_message(update, f"Ошибка: {e}")

if TELEGRAM_API_TOKEN is None:
    print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
    exit(1)

telegram_bot = TelegramBot(TELEGRAM_API_TOKEN)
telegram_bot.register_command("start", "Получить список команд бота", start)
telegram_bot.register_command("createCal", "Создать календарь", start_JSON)
telegram_bot.register_command("listIcsFiles", "Получить список календарей", list_ics_files)
telegram_bot.register_command("DownUserFilCal", "Получить список календарей с возможностью скачивания", list_ics_files_down)

asyncio.run(telegram_bot.run())