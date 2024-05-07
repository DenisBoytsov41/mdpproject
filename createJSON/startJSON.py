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
        subprocess.run([PYTHON_EXE, START_CREATE_CAL_SCRIPT, output_json_file], check=True)
        output_dir = os.path.dirname(output_json_file)
        ical_dir = os.path.join(output_dir, "ICAL")

        json_file_name = os.path.basename(output_json_file)
        json_file_prefix = os.path.splitext(json_file_name)[0]

        ics_files = [f for f in os.listdir(ical_dir) if f.startswith(json_file_prefix) and f.endswith(".ics")]

        if ics_files:
            ics_file_path = os.path.join(ical_dir, ics_files[0])
            subprocess.run([PYTHON_EXE, GOOGLE_CAL, ics_file_path], check=True)
        else:
            print("Нет файлов формата .ics в папке ICAL.")

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
