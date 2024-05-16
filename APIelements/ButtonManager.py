# -*- coding: utf-8 -*-
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

class ButtonPaginator:
    def __init__(self, buttons, telegram_api_token, command=None, callback_command='button'):
        self.buttons = buttons
        self.telegram_api_token = telegram_api_token
        self.command = command
        self.callback_command = callback_command
        self.flag = False

    async def start_paginator(self, update, bot):
        self.flag = True
        await self.start(update, bot)

    def paginate_buttons(self, page_size=5):
        paginated_buttons = []
        for i in range(0, len(self.buttons), page_size):
            paginated_buttons.append(self.buttons[i:i+page_size])
        return paginated_buttons

    async def send_buttons_page(self, chat_id, buttons_page, bot, page, total_pages):
        text = f"Страница {page}/{total_pages}:"
        reply_markup = InlineKeyboardMarkup(buttons_page)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    async def handle_pagination(self, query, chat_id, bot, page=1, page_size=15, total_page_buttons=8):
        total_pages = (len(self.buttons) + page_size - 1) // page_size
        if page < 1 or page > total_pages:
            await bot.send_message(chat_id=chat_id, text="Недопустимый номер страницы")
            return
        start_page = max(1, min(page - total_page_buttons // 2, total_pages - total_page_buttons + 1))
        end_page = min(start_page + total_page_buttons - 1, total_pages)
        # Определяем диапазон кнопок страниц для отображения
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, len(self.buttons))
        buttons_page = self.buttons[start_index:end_index]

        # Разбиваем кнопки на строки
        rows = []
        row = []
        for button in buttons_page:
            row.append(button[0])
            if len(row) == 5:
                rows.append(row)
                row = []

        # Добавляем навигационные кнопки
        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("Назад", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("Вперед", callback_data=f"next_page_{page}"))
        rows.append(navigation_buttons)

        # Добавляем кнопки для перехода к определенной странице
        page_buttons = [InlineKeyboardButton(str(i), callback_data=f"page_{i}") for i in
                        range(start_page, end_page + 1) if i != page]

        rows.append(page_buttons)

        if query is not None:
            await self.send_buttons_page(query.message.chat.id, rows, bot, page, total_pages)
        else:
            await self.send_buttons_page(chat_id, rows, bot, page, total_pages)

    async def start(self, chat_id, bot):
        # Отображаем первую страницу кнопок при получении команды /start
        query = None
        await self.handle_pagination(query, chat_id, bot)

    async def handle_button_press(self, query, update, bot):
        data = query.data.split('_')
        if len(data) >= 3:
            page = int(data[2])
        elif len(data) == 1:
            page = 0
        else:
            page = int(data[1])
        if data[0] == 'prev' and page > 1:
            await self.handle_pagination(query, update.effective_chat.id, bot, page - 1)
        elif data[0] == 'next':
            await self.handle_pagination(query, update.effective_chat.id, bot, page + 1)
        elif data[0] == 'page':
            page_to_load = int(data[1])
            await self.handle_pagination(query, update.effective_chat.id, bot, page_to_load)
        else:
            button_number = int(data[0].replace(self.callback_command, ''))
            await bot.send_message(chat_id=query.message.chat.id, text=f"Нажата кнопка {button_number}")

    async def run(self):
        bot = Bot(token=self.telegram_api_token)
        await bot.initialize()
        max_update_id = 0

        while True:
            try:
                updates = await bot.get_updates(offset=max_update_id + 1, timeout=60)
                for update in updates:
                    if update.message:
                        if self.command is not None:
                            if update.message.text.startswith(self.command):
                                self.flag = False
                                await self.start(update.effective_chat.id, bot)
                                max_update_id = update.update_id
                        else:
                            if self.flag:
                                self.flag = False
                                await self.start(update.effective_chat.id, bot)
                                max_update_id = update.update_id
                    elif update.callback_query:
                        query = update.callback_query
                        await self.handle_button_press(query, update, bot)
                        max_update_id = update.update_id
            except Exception as e:
                print(f"Error in main loop: {e}")
            await asyncio.sleep(1)
