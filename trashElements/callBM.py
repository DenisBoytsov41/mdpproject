# -*- coding: utf-8 -*-
import asyncio
from ButtonManager import ButtonPaginator
from telegram import InlineKeyboardButton
from config import *

async def main():
    buttons = []
    for i in range(1, 401):
        button = InlineKeyboardButton(f"Кнопка {i}", callback_data=f"button{i}")
        buttons.append([button])

    paginator = ButtonPaginator(buttons, TELEGRAM_API_TOKEN, command='/start')
    await paginator.run()

if __name__ == "__main__":
    asyncio.run(main())
