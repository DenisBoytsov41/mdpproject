import asyncio
from telegram import Bot
from commands import handle_commands
from config import TELEGRAM_API_TOKEN


async def main():
    bot = Bot(token=TELEGRAM_API_TOKEN)
    await bot.initialize()

    offset_dict = {}  # Словарь для хранения offset для каждого чата

    while True:
        updates = await bot.get_updates(timeout=60)
        for update in updates:
            if update.message:
                chat_id = update.message.chat_id
                offset = offset_dict.get(chat_id, 0)

                if update.update_id >= offset:
                    await handle_commands(update, bot)
                    offset_dict[chat_id] = update.update_id + 1  # Обновляем offset для текущего чата

        await asyncio.sleep(1)


if __name__ == "__main__":
    if TELEGRAM_API_TOKEN is None:
        print("Ошибка: Не удалось найти токен Telegram API в переменной окружения TELEGRAM_API_TOKEN")
        exit(1)

    asyncio.run(main())
