import os
import json
import asyncio
import subprocess
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.error import BadRequest
from config import *

# Класс TelegramBot представляет бота Telegram, который управляет командами и взаимодействием с пользователями
class TelegramBot:
    def __init__(self, token):
        """
            Инициализация объекта бота Telegram.

            Args:
                token (str): Токен бота.
        """
        self.bot = Bot(token=token)
        self.commands = {}
        self.user_button_state = {}

    # Регистрирует новую команду для бота
    def register_command(self, command, description, handler):
        """
        Регистрирует новую команду для бота.

        Args:
            command (str): Название команды.
            description (str): Описание команды.
            handler (function): Функция-обработчик команды.
        """
        self.commands[command] = (description, handler)

    # Отправляет сообщение пользователю
    async def send_telegram_message(self, update: Update, message: str):
        """
        Отправляет сообщение пользователю.

        Args:
            update (Update): Объект обновления от Telegram.
            message (str): Текст сообщения.
        """
        if update.message is not None:
            await self.bot.send_message(chat_id=update.message.chat_id, text=message)
        else:
            await self.bot.send_message(chat_id=update.callback_query.message.chat.id, text=message)

    # Отправляет сообщение в указанный чат.
    async def send_telegram_message_2(self, chat_id, message: str):
        """
           Отправляет сообщение в указанный чат.

           Args:
               chat_id (str): Идентификатор чата.
               message (str): Текст сообщения.
        """
        await self.bot.send_message(chat_id=chat_id, text=message)

    # Обрабатывает нажатие кнопки в сообщении
    async def handle_button_press(self, update: Update):
        """
        Обрабатывает нажатие кнопки в сообщении.

        Args:
            update (Update): Объект обновления от Telegram.
        """
        query = update.callback_query
        user_id = query.from_user.id
        button_id = query.data

        if button_id == 'create_cal':
            if self.user_button_state.get(user_id, {}).get(button_id, False):
                await self.send_telegram_message_2(query.message.chat.id, "Вы уже выбрали создание календаря")
                try:
                    await query.answer(cache_time=30)
                except BadRequest as e:
                    print(f"Ошибка ответа на запрос обратного вызова: {e}")
                return
            await self.send_telegram_message_2(query.message.chat.id, "Вы выбрали создание календаря")
            self.user_button_state.setdefault(user_id, {})[button_id] = True
            update_json = update.to_dict()
            update_json_str = json.dumps(update_json)
            await asyncio.create_task(self.handle_create_cal(update, update_json_str))
            try:
                await query.answer(cache_time=30)
            except BadRequest as e:
                print(f"Ошибка ответа на запрос обратного вызова: {e}")
        elif button_id.startswith('download_'):
            await self.handle_download_file(update)

    # Запускает создание календаря, выполняя внешнюю команду
    async def handle_create_cal(self, update: Update, update_json_str: str):
        """
        Запускает создание календаря, выполняя внешнюю команду.

        Args:
            update (Update): Объект обновления от Telegram.
            update_json_str (str): JSON-строка с данными обновления.
        """
        try:
            subprocess.run([PYTHON_EXE, START_CREATE_JSON_SCRIPT, update_json_str, TELEGRAM_API_TOKEN, str(update.effective_user.id)], check=True)
        except Exception as e:
            await self.send_telegram_message(update, f"Ошибка: {e}")
        finally:
            self.user_button_state.setdefault(update.effective_user.id, {})['create_cal'] = False

    # Обрабатывает запрос на скачивание файла
    async def handle_download_file(self, update: Update):
        """
        Обрабатывает запрос на скачивание файла.

        Args:
            update (Update): Объект обновления от Telegram.
        """
        query = update.callback_query
        user_id = query.from_user.id
        button_data = query.data

        if button_data.startswith('download_'):
            identifier = button_data.replace('download_', '')
            file_path = None

            for root, _, files in os.walk(CREATE_JSON_DIR_ICAL):
                for file in files:
                    parts = file.split('__')
                    if len(parts) >= 3:
                        file_identifier = f"{parts[0].split('_')[1]}_{parts[2]}"
                    else:
                        file_identifier = file

                    if file_identifier == identifier:
                        file_path = os.path.join(root, file)
                        break
                if file_path:
                    break

            try:
                if file_path:
                    with open(file_path, 'rb') as file:
                        await self.bot.send_document(chat_id=query.message.chat.id, document=InputFile(file),
                                                filename=os.path.basename(file_path))
                    await query.answer()
                else:
                    await self.send_telegram_message_2(query.message.chat.id, f"Файл с идентификатором {identifier} не найден.")
            except FileNotFoundError:
                await self.send_telegram_message_2(query.message.chat.id, f"Файл с идентификатором {identifier} не найден.")
            except Exception as e:
                await self.send_telegram_message_2(query.message.chat.id, f"Ошибка: {e}")

    # Обрабатывает команды, отправленные пользователем.
    async def command_handler(self, update: Update, offset_dict: dict):
        """
        Обрабатывает команды, отправленные пользователем.

        Args:
            update (Update): Объект обновления от Telegram.
            offset_dict (dict): Словарь для отслеживания обработанных команд.
        """

        current_time = time.time()
        print("Получено обновление:", update.message.text)
        command = update.message.text.split()[0][1:]
        if command in self.commands:
            print(f"Получена команда /{command}")
            last_command_update_id = offset_dict.get(update.message.chat_id, 0)
            if update.update_id != last_command_update_id:
                description, handler = self.commands[command]
                await handler(update, self)  # Передаем self как bot
                offset_dict[update.message.chat_id] = update.update_id
            else:
                await self.send_telegram_message(update, "Пожалуйста, подождите 10 секунд перед отправкой следующей команды")
        else:
            print("Неизвестная команда")
            await self.send_telegram_message(update, "Неизвестная команда")

    # Основной цикл бота, который получает и обрабатывает обновления от Telegram
    async def run(self):
        """Основной цикл бота, который получает и обрабатывает обновления от Telegram"""
        await self.bot.initialize()
        offset_dict = {}
        max_update_id = 0
        while True:
            updates = await self.bot.get_updates(offset=max_update_id + 1, timeout=60)
            for update in updates:
                if update.message:
                    await asyncio.create_task(self.command_handler(update, offset_dict))
                    max_update_id = update.update_id
                elif update.callback_query:
                    await asyncio.create_task(self.handle_button_press(update))
                    max_update_id = update.update_id
            await asyncio.sleep(1)
