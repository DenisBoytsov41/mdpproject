import asyncio
import json
import subprocess
import sys
from telegram import Update
from webdriver_setup import setup_driver
from schedule import select_schedule
from telegram import Bot
from config import *
from telegram_utils import send_telegram_message, get_telegram_input


async def main(update, bot_context):
    driver = setup_driver()
    try:
        driver.get("https://timetable.ksu.edu.ru/")
        bot = Bot(token=bot_context)
        await bot.initialize()
        schedule_json, output_json_file = await select_schedule(bot, driver, update)
        print(json.dumps(schedule_json))
        subprocess.run([PYTHON_EXE, START_CREATE_CAL_SCRIPT, output_json_file, schedule_json], check=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Недостаточно аргументов. Укажите update_data.")
        sys.exit(1)

    update_data = json.loads(sys.argv[1])
    update = Update.de_json(update_data, None)

    bot_context = sys.argv[2]
    asyncio.run(main(update, bot_context))
