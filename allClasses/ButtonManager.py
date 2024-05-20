# -*- coding: utf-8 -*-
import asyncio
import uuid

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from datetime import datetime, timedelta

# Класс ButtonPaginator представляет пагинатор кнопок для Telegram бота
class ButtonPaginator:
    """buttons: Список кнопок.
    telegram_api_token: Токен API Telegram.
    user_id: Идентификатор пользователя.
    command: Команда для активации пагинатора.
    callback_command: Команда для обработки нажатия кнопки."""
    def __init__(self, buttons, telegram_api_token, user_id, command=None, callback_command='button'):
        self.buttons = buttons
        self.telegram_api_token = telegram_api_token
        self.user_id = user_id
        self.command = command
        self.callback_command = callback_command
        self.flag = False
        self.button_pressed = None
        self.update = None
        self.last_callback_time = datetime.now()
        self.pressed_buttons = {}  # Сохраняем нажатые кнопки
        self.session_id = None
        self.previous_callback = None

    # Запускает пагинатор кнопок
    async def start_paginator(self, update, bot):
        """update: Объект обновления от Telegram.
        bot: Объект бота."""
        self.flag = True
        await self.start(update, bot)

    # Останавливает пагинатор кнопок
    async def stop(self):
        """Останавливает работу пагинатора."""
        self.flag = False
        await asyncio.gather(*asyncio.all_tasks())

    # Очищает состояние пагинатора
    def clear_state(self):
        """Очищает состояние пагинатора."""
        self.flag = False
        self.button_pressed = None
        self.update = None
        self.last_callback_time = datetime.now()
        self.pressed_buttons.clear()
        self.previous_callback = None

    # Разбивает кнопки на страницы
    def paginate_buttons(self, page_size=5):
        """page_size: Количество кнопок на странице."""
        paginated_buttons = []
        for i in range(0, len(self.buttons), page_size):
            paginated_buttons.append(self.buttons[i:i + page_size])
        return paginated_buttons

    # Отправляет страницу кнопок в чат
    async def send_buttons_page(self, chat_id, buttons_page, bot, page, total_pages):
        """chat_id: Идентификатор чата.
        buttons_page: Страница кнопок.
        bot: Объект бота.
        page: Номер текущей страницы.
        total_pages: Общее количество страниц."""

        text = f"Страница {page}/{total_pages}:"
        reply_markup = InlineKeyboardMarkup(buttons_page)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    # Обрабатывает пагинацию кнопок
    async def handle_pagination(self, query, chat_id, bot, page=1, page_size=10, total_page_buttons=8):
        """query: Объект запроса кнопки.
        chat_id: Идентификатор чата.
        bot: Объект бота.
        page: Номер текущей страницы.
        page_size: Количество кнопок на странице.
        total_page_buttons: Общее количество кнопок на странице."""

        total_pages = (len(self.buttons) + page_size - 1) // page_size
        if page < 1 or page > total_pages:
            await self.handle_invalid_page(chat_id, bot)
            return

        start_page, end_page = self.calculate_page_range(page, total_pages, total_page_buttons)
        buttons_page, button_last = self.get_buttons_for_page(page, page_size)
        rows = self.split_buttons_into_rows(buttons_page, button_last)

        navigation_buttons = self.generate_navigation_buttons(page, total_pages)
        rows.append(navigation_buttons)

        page_buttons = self.generate_page_navigation_buttons(start_page, end_page, page)
        rows.append(page_buttons)
        rows.append(button_last)

        if query is not None:
            await self.send_buttons_page(query.message.chat.id, rows, bot, page, total_pages)
        else:
            await self.send_buttons_page(chat_id, rows, bot, page, total_pages)

    # Обрабатывает случай, когда номер страницы недопустим.
    async def handle_invalid_page(self, chat_id, bot):
        """chat_id: Идентификатор чата.
        bot: Объект бота."""
        await bot.send_message(chat_id=chat_id, text="Недопустимый номер страницы")

    # Вычисляет диапазон страниц для отображения
    def calculate_page_range(self, page, total_pages, total_page_buttons):
        """page: Номер текущей страницы.
        total_pages: Общее количество страниц.
        total_page_buttons: Общее количество кнопок на странице."""
        start_page = max(1, min(page - total_page_buttons // 2, total_pages - total_page_buttons + 1))
        end_page = min(start_page + total_page_buttons - 1, total_pages)
        return start_page, end_page

    # Получает кнопки для конкретной страницы
    def get_buttons_for_page(self, page, page_size):
        """page: Номер текущей страницы.
        page_size: Количество кнопок на странице."""
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, len(self.buttons))
        buttons_page = self.buttons[start_index:end_index]
        button_last = self.buttons[-1]
        return buttons_page, button_last

    # Разбивает кнопки на строки для отображения в сообщении.
    def split_buttons_into_rows(self, buttons_page, button_last):
        """buttons_page: Страница кнопок.
        button_last: Последняя кнопка."""
        rows = []
        row = []
        len_buttons_page = len(buttons_page)
        for button in buttons_page:
            row.append(button[0])
            if (len(row) == 1 or (len_buttons_page < 1 and len(row) < 1 and len_buttons_page == len(row))) \
                    and button_last != button:
                rows.append(row)
                row = []
                len_buttons_page -= 1
        return rows

    # Генерирует кнопки навигации "Назад" и "Вперед"
    def generate_navigation_buttons(self, page, total_pages):
        """page: Номер текущей страницы.
        total_pages: Общее количество страниц."""
        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("Назад", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("Вперед", callback_data=f"next_page_{page}"))
        return navigation_buttons

    # Генерирует кнопки для перехода к определенной странице
    def generate_page_navigation_buttons(self, start_page, end_page, current_page):
        """start_page: Номер первой страницы в диапазоне.
        end_page: Номер последней страницы в диапазоне.
        current_page: Номер текущей страницы."""
        page_buttons = [InlineKeyboardButton(str(i), callback_data=f"page_{i}") for i in range(start_page, end_page + 1)
                        if i != current_page]
        return page_buttons

    async def start(self, chat_id, bot):
        query = None
        await self.handle_pagination(query, chat_id, bot)

    # Главный метод, который обрабатывает нажатие кнопки. Определяет,
    # является ли запрос действительным, извлекает номер страницы и направляет обработку на соответствующий метод.
    async def handle_button_press(self, query, update2, bot):
        """query: Объект запроса кнопки.
        update2: Объект обновления от Telegram.
        bot: Объект бота."""
        if not self.is_valid_query(query):
            return None

        data = query.data.split('_')
        page = self.extract_page_number(data)

        if query.id == self.session_id:
            print("Я попал сюда")
            return None

        if data[0] in ['prev', 'next', 'page'] and isinstance(page, int):
            await self.handle_pagination_commands(data[0], query, bot, page)
        elif len(update2.callback_query.data.split('_')) == 2 and update2.callback_query.data.split('_')[
            1] == self.callback_command:
            await bot.send_message(chat_id=query.message.chat.id, text="Возвращаемся к предыдущему запросу...")
            return query.data
        else:
            return await self.handle_custom_command(data, query, bot)

    # Обрабатывает команды пагинации (предыдущая, следующая страница и конкретная страница).
    async def handle_pagination_commands(self, command, query, bot, page):
        """command: Тип команды (prev, next, page).
        query: Объект запроса кнопки.
        bot: Объект бота.
        page: Номер текущей страницы."""
        if command == 'prev' and page > 1:
            await self.handle_pagination(query, query.message.chat.id, bot, page - 1)
        elif command == 'next':
            await self.handle_pagination(query, query.message.chat.id, bot, page + 1)
        elif command == 'page':
            await self.handle_pagination(query, query.message.chat.id, bot, page)

    # Проверяет, является ли запрос действительным (не пустым и содержит данные).
    def is_valid_query(self, query):
        """query: Объект запроса кнопки."""
        return query is not None and query.data is not None

    # Извлекает номер страницы из данных запроса.
    def extract_page_number(self, data):
        """data: Данные запроса."""
        if len(data) >= 3:
            return int(data[2]) if data[2].isdigit() else data[2]
        elif len(data) == 1:
            return 0
        else:
            return int(data[1]) if data[1].isdigit() else data[1]

    # Обрабатывает пользовательские команды, связанные с определенными кнопками.
    async def handle_custom_command(self, data, query, bot):
        """data: Данные запроса.
        query: Объект запроса кнопки.
        bot: Объект бота."""
        if self.callback_command in data[0]:
            button_number = int(data[0].replace(self.callback_command, ''))
            if self.is_button_already_pressed(button_number):
                await bot.send_message(chat_id=query.message.chat.id, text=f"Кнопка {button_number} уже была нажата")
                return None
            await self.register_button_press(button_number, query, bot)
            return button_number
        else:
            return None

    # Проверяет, была ли кнопка уже нажата пользователем.
    def is_button_already_pressed(self, button_number):
        """button_number: Номер кнопки."""
        if self.user_id not in self.pressed_buttons:
            self.pressed_buttons[self.user_id] = set()
        return button_number in self.pressed_buttons[self.user_id]

    # Регистрирует нажатие кнопки и отправляет сообщение пользователю.
    async def register_button_press(self, button_number, query, bot):
        """button_number: Номер кнопки.
        query: Объект запроса кнопки.
        bot: Объект бота."""
        self.pressed_buttons[self.user_id].add(button_number)
        await bot.send_message(chat_id=query.message.chat.id, text=f"Нажата кнопка {button_number}")
        self.button_pressed = button_number
        self.session_id = query.id

    # Обрабатывает callback_query
    async def handle_callback_query(self, query, update, bot):
        """query: Объект запроса кнопки.
        update: Объект обновления от Telegram.
        bot: Объект бота."""
        if query is None:
            return None

        current_time = datetime.now()
        if (current_time - self.last_callback_time).total_seconds() > 30:
            #await bot.send_message(chat_id=query.message.chat.id, text="Запрос устарел")
            self.clear_state()
            return None
        self.previous_callback = query.data

        press = await self.handle_button_press(query, update, bot)
        return press

    # Запускает пагинатор и обрабатывает обновления
    async def run(self, processed_updates=None):
        """processed_updates: Обработанные обновления."""
        bot = await self.initialize_bot()
        max_update_id = 0

        while True:
            try:
                updates = await self.fetch_updates(bot, max_update_id)
                for update in updates:
                    if update.message:
                        callback = await self.handle_message(update, bot, processed_updates)
                        if callback is not None:
                            return callback
                    elif update.callback_query:
                        callback = await self.process_incoming_callback(update, bot, processed_updates)
                        if callback is not None:
                            return callback
                if updates:
                    max_update_id = updates[-1].update_id
            except Exception as e:
                print(f"Error in main loop: {e}")
            await asyncio.sleep(1)

    # Инициализирует объект бота
    async def initialize_bot(self):
        """Инициализирует объект бота."""
        bot = Bot(token=self.telegram_api_token)
        await bot.initialize()
        return bot

    # Получает обновления от Telegram
    async def fetch_updates(self, bot, max_update_id):
        """bot: Объект бота.
        max_update_id: Максимальный идентификатор обновления."""
        updates = await bot.get_updates(offset=max_update_id + 1, timeout=60)
        return updates

    # Обрабатывает сообщения от пользователя
    async def handle_message(self, update, bot, processed_updates):
        """update: Объект обновления от Telegram.
        bot: Объект бота.
        processed_updates: Обработанные обновления."""
        if self.command is not None and update.message.text.startswith(self.command):
            if self.is_new_update(update.message.message_id, processed_updates):
                await self.process_command(update, bot)
                self.update = update
        elif self.flag:
            if self.is_new_update(update.message.message_id, processed_updates):
                await self.process_command(update, bot)
                self.update = update

    # Обрабатывает команду от пользователя
    async def process_command(self, update, bot):
        """update: Объект обновления от Telegram.
        bot: Объект бота."""
        self.flag = False
        await self.start(update.effective_chat.id, bot)

    # Проверяет, является ли обновление новым
    def is_new_update(self, message_id, processed_updates):
        """message_id: Идентификатор сообщения.
        processed_updates: Обработанные обновления."""
        return processed_updates is None or message_id not in processed_updates

    # Обрабатывает callback_query от пользователя
    async def process_incoming_callback(self, update, bot, processed_updates):
        """update: Объект обновления от Telegram.
        bot: Объект бота.
        processed_updates: Обработанные обновления."""
        if self.is_new_update(update.callback_query.message.message_id, processed_updates):
            query = update.callback_query
            self.update = update
            current_time = datetime.now()
            return await self.process_callback(update, query, bot, current_time)

    # Обрабатывает callback от кнопки
    async def process_callback(self, update, query, bot, current_time):
        """update: Объект обновления от Telegram.
        query: Объект запроса кнопки.
        bot: Объект бота.
        current_time: Текущее время."""
        if (current_time - self.last_callback_time).total_seconds() > 30:
            self.clear_state()
            return

        if self.previous_callback == query.data:
            return

        total = query.data.split('_')
        comm = total[0] if len(total) >= 2 else None

        if comm in ['prev', 'next', 'page']:
            await self.handle_button_press(query, self.update, bot)
            self.last_callback_time = current_time
            self.previous_callback = query.data
            self.update = update
            return None

        if query.data not in ['start', 'createCal', 'create_cal']:
            total_1 = total[1] if len(total) >= 2 else None
            if self.callback_command in query.data or total_1 == self.callback_command:
                return await self.wait_for_press(query, update, bot, current_time)

    # Ожидает нажатия кнопки
    async def wait_for_press(self, query, update, bot, current_time):
        """query: Объект запроса кнопки.
        update: Объект обновления от Telegram.
        bot: Объект бота.
        current_time: Текущее время."""
        press = None
        while press is None:
            self.update = update
            press = await self.handle_button_press(query, self.update, bot)
            print(press)
            await asyncio.sleep(1)
        self.last_callback_time = current_time
        self.previous_callback = query.data
        self.update = update
        return press