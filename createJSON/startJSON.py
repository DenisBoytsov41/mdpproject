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
from db.db_operations import create_users_tables_table, add_user_table_entry


async def main(update, bot_context, user_id):
    if update is None:
        print("Ошибка: Объект update не был передан.")
        return

    driver = setup_driver()
    try:
        driver.get("https://timetable.ksu.edu.ru/")
        bot = Bot(token=bot_context)
        await bot.initialize()
        schedule_json, output_json_file = await select_schedule(bot, driver, update, user_id)
        if output_json_file is None:
            await send_telegram_message(update, "Произошла ошибка при выполнении команды. output_json_file не был создан.")
            return
        subprocess.run([PYTHON_EXE, START_CREATE_CAL_SCRIPT, output_json_file], check=True)
        output_dir = os.path.dirname(output_json_file)
        ical_dir = os.path.join(output_dir, "ICAL")

        json_file_name = os.path.basename(output_json_file)
        json_file_prefix = os.path.splitext(json_file_name)[0]

        ics_files = [f for f in os.listdir(ical_dir) if f.startswith(json_file_prefix) and f.endswith(".ics")]

        if ics_files:
            ics_file_path = os.path.join(ical_dir, ics_files[0])
            update_data_str = json.dumps(update_data)
            subprocess.run([PYTHON_EXE, GOOGLE_CAL, ics_file_path, update_data_str, bot_context], check=True)
            create_users_tables_table()
            table_name = os.path.splitext(os.path.basename(ics_file_path))[0]
            if table_name:
                add_user_table_entry(update.effective_user.id, table_name)
        else:
            await send_telegram_message(update, "Нет файлов формата .ics в папке ICAL.")

    except Exception as e:
        error_message = f"Произошла ошибка при выполнении команды. {e}"
        await send_telegram_message(update, error_message)

    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Недостаточно аргументов. Укажите update_data.")
        sys.exit(1)

    update_data = json.loads(sys.argv[1])
    update = Update.de_json(update_data, None)

    bot_context = sys.argv[2]
    user_id = sys.argv[3]
    asyncio.run(main(update, bot_context, user_id))