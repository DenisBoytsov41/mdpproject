# -*- coding: utf-8 -*-
import asyncio
import uuid

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from datetime import datetime, timedelta


class ButtonPaginator:
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

    async def start_paginator(self, update, bot):
        self.flag = True
        await self.start(update, bot)
    async def stop(self):
        self.flag = False
        await asyncio.gather(*asyncio.all_tasks())

    def clear_state(self):
        self.flag = False
        self.button_pressed = None
        self.update = None
        self.last_callback_time = datetime.now()
        self.pressed_buttons.clear()

    def paginate_buttons(self, page_size=5):
        paginated_buttons = []
        for i in range(0, len(self.buttons), page_size):
            paginated_buttons.append(self.buttons[i:i + page_size])
        return paginated_buttons

    async def send_buttons_page(self, chat_id, buttons_page, bot, page, total_pages):
        text = f"Страница {page}/{total_pages}:"
        reply_markup = InlineKeyboardMarkup(buttons_page)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_pagination(self, query, chat_id, bot, page=1, page_size=10, total_page_buttons=8):
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
        len_buttons_page = len(buttons_page)
        for button in buttons_page:
            row.append(button[0])
            if len(row) == 1 or (len_buttons_page<1 and len(row) < 1 and len_buttons_page == len(row)):
                rows.append(row)
                row = []
                len_buttons_page -=1

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
        query = None
        await self.handle_pagination(query, chat_id, bot)

    async def handle_button_press(self, query, update2, bot):
        if query is None or query.data is None:
            return None

        data = query.data.split('_')
        if query.id == self.session_id:
            print("Я попал сюда")
            return None

        if len(data) >= 3:
            page = int(data[2])
        elif len(data) == 1:
            page = 0
        else:
            page = int(data[1])

        if data[0] == 'prev' and page > 1:
            await self.handle_pagination(query, query.message.chat.id, bot, page - 1)
        elif data[0] == 'next':
            await self.handle_pagination(query, query.message.chat.id, bot, page + 1)
        elif data[0] == 'page':
            page_to_load = int(data[1])
            await self.handle_pagination(query, query.message.chat.id, bot, page_to_load)
        else:
            # Проверяем, содержится ли часть callback_command в data[0]
            if self.callback_command in data[0]:
                button_number = int(data[0].replace(self.callback_command, ''))
                if self.user_id not in self.pressed_buttons:
                    self.pressed_buttons[self.user_id] = set()
                if button_number in self.pressed_buttons[self.user_id]:
                    await bot.send_message(chat_id=query.message.chat.id,
                                           text=f"Кнопка {button_number} уже была нажата")
                    return None
                self.pressed_buttons[self.user_id].add(button_number)
                await bot.send_message(chat_id=query.message.chat.id, text=f"Нажата кнопка {button_number}")
                self.button_pressed = button_number
                self.session_id = query.id
                return button_number
            else:
                return None

    async def handle_callback_query(self, query, update, bot):
        if query is None:
            return None

        current_time = datetime.now()
        if (current_time - self.last_callback_time).total_seconds() > 30:
            await bot.send_message(chat_id=query.message.chat.id, text="Запрос устарел")
            self.clear_state()
            return None

        press = await self.handle_button_press(query, update, bot)
        return press

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
                                self.update = update
                        else:
                            if self.flag:
                                self.flag = False
                                await self.start(update.effective_chat.id, bot)
                                max_update_id = update.update_id
                                self.update = update
                    elif update.callback_query:
                        query = update.callback_query
                        self.update = update
                        current_time = datetime.now()
                        if (current_time - self.last_callback_time).total_seconds() > 30:
                            await bot.send_message(chat_id=query.message.chat.id, text=f"Запрос устарел")
                            self.clear_state()
                            continue
                        total = update.callback_query.data.split('_')
                        comm = None
                        if len(total) == 3:
                            comm = total[0]
                        elif len(total) == 2:
                            comm = total[0]
                        if comm in ['prev', 'next', 'page']:
                            self.update = update
                            await self.handle_button_press(query, self.update, bot)
                            max_update_id = update.update_id
                            self.last_callback_time = current_time
                        if update.callback_query.data not in ['start', 'createCal', 'create_cal']:
                            if self.callback_command in update.callback_query.data:
                                press = None
                                while press is None:
                                    self.update = update
                                    press = await self.handle_button_press(query, self.update, bot)
                                    print(press)
                                    await asyncio.sleep(1)
                                max_update_id = update.update_id
                                self.last_callback_time = current_time
                                return press
            except Exception as e:
                print(f"Error in main loop: {e}")
            await asyncio.sleep(1)
