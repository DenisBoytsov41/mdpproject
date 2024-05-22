# -*- coding: utf-8 -*-
import json
import os
import sys
import asyncio
from telegram import Bot, Update
from allClasses.GoogleCalendarManager import GoogleCalendarManager

CLIENT_SECRETS_FILE = 'credentials.json'
authorization_response = None

def get_ics_file_path():
    """
    Получает путь к файлу .ics из аргументов командной строки или запрашивает у пользователя.
    """
    subprocess_ics_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    if subprocess_ics_file_path:
        return subprocess_ics_file_path
    else:
        return input("Введите путь к файлу .ics: ")

def get_update_and_bot_context():
    """
    Получает данные обновления Telegram и контекст бота из аргументов командной строки.
    """
    update_data_str = sys.argv[2] if len(sys.argv) > 2 else None
    bot_context = sys.argv[3] if len(sys.argv) > 3 else None
    update = None
    bot = None
    if update_data_str is not None:
        update_data = json.loads(update_data_str)
        update = Update.de_json(update_data, None)
    if bot_context is not None:
        bot = Bot(token=bot_context)
    return update, bot

def get_user_id_from_update(update):
    """
    Получает идентификатор пользователя из объекта обновления Telegram.
    """
    user_id = None
    if update.message is not None:
        user_id = update.message.chat_id
    if user_id is None and update.callback_query is not None:
        user_id = update.callback_query.message.chat.id
    return user_id
async def process_ics_file(manager, service, ics_file_path, bot, user_id):
    """
    Обрабатывает файл .ics и добавляет события в Google Календарь.
    """
    await manager.send_telegram_message(bot, user_id, [
        "Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря."])
    # print("Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря.")
    await manager.add_events_to_google_calendar(service, ics_file_path)
    await manager.send_telegram_message(bot, user_id,
                                        ["События успешно добавлены в календарь Google."])
    # print("События успешно добавлены в календарь Google.")
async def main():
    ics_file_path = get_ics_file_path()
    update, bot = get_update_and_bot_context()
    if bot:
        await bot.initialize()
    if os.path.exists(ics_file_path):
        manager = GoogleCalendarManager()
        service = await manager.authenticate_google_calendar(bot, update)
        user_id = get_user_id_from_update(update)
        if service:
            await process_ics_file(manager, service, ics_file_path, bot, user_id)
        else:
            await manager.send_telegram_message(bot, user_id,
                                        ["Не удалось выполнить аутентификацию."])
            #print("Не удалось выполнить аутентификацию.")
    else:
        print("Указанный файл не существует.")


if __name__ == "__main__":
    asyncio.run(main())
