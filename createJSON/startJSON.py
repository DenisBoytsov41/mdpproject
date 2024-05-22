import asyncio
import json
import subprocess
import sys
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from allClasses.ScheduleBotHandler import ScheduleBotHandler
from telegram import Bot
from config import *
from createJSON.utils import send_telegram_message, setup_driver
from db.db_operations import create_users_tables_table, add_user_table_entry


processed_messages = []
async def main(update, bot_context, user_id):
    """Основной метод для работы с JSON календаря
    Args:
        update (Update): Обновление от Telegram.
        bot_context (str): Контекст бота.
        user_id (str): ID пользователя.

    Returns:
        None
    """
    if update is None:
        print("Ошибка: Объект update не был передан.")
        return

    driver = setup_driver()
    try:
        driver, bot, schedule_json, output_json_file = await initialize_bot_and_driver(driver,bot_context)
        subprocess.run([PYTHON_EXE, START_CREATE_CAL_SCRIPT, output_json_file], check=True)
        output_dir = os.path.dirname(output_json_file)
        ical_dir = os.path.join(output_dir, "ICAL")

        json_file_name = os.path.basename(output_json_file)
        json_file_prefix = os.path.splitext(json_file_name)[0]

        ics_files = [f for f in os.listdir(ical_dir) if f.startswith(json_file_prefix) and f.endswith(".ics")]
        if ics_files:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Добавить расписание в ваш календарь", callback_data="add_calendar")],
                [InlineKeyboardButton("Получить файл .ical", callback_data="get_ical_file")]
            ])
            await process_calendar_actions(bot,ical_dir,ics_files,user_id, keyboard,update_data)
        else:
            await send_telegram_message(update, "Нет файлов формата .ics в папке ICAL.")

    except Exception as e:
        error_message = f"Произошла ошибка при выполнении команды. {e}"
        await send_telegram_message(update, error_message)

    finally:
        driver.quit()

async def initialize_bot_and_driver(driver,bot_context):
    """
    Инициализирует бота и веб-драйвер, а также обрабатывает успешный или неудачный запрос на получение расписания.
    Args:
        driver: Веб-драйвер.
        bot_context (str): Контекст бота.

    Returns:
        Tuple: Кортеж из объекта веб-драйвера, бота, расписания в json формате, а также путь до этого файла.
    """
    driver.get("https://timetable.ksu.edu.ru/")
    bot = Bot(token=bot_context)
    await bot.initialize()
    try:
        manager = ScheduleBotHandler()
        schedule_json, output_json_file = await manager.get_dom_element(bot, driver, update, user_id)
        if output_json_file is None:
            await send_telegram_message(update,
                                        "Произошла ошибка при выполнении команды. output_json_file не был создан.")
            return
    except Exception as e:
        manager = ScheduleBotHandler()
        schedule_json, output_json_file = await manager.back_schedule(bot, driver, update, user_id)
        if output_json_file is None:
            await send_telegram_message(update,
                                        "Произошла ошибка при выполнении команды. output_json_file не был создан.")
            return
    return driver, bot, schedule_json, output_json_file
async def process_calendar_actions(bot,ical_dir,ics_files,user_id, keyboard,update_data):
    """
    Обрабатывает действия пользователя с календарем.
    Args:
        bot (Bot): Объект бота.
        ical_dir (str): Путь к папке с файлами .ics.
        ics_files (list): Список файлов .ics.
        user_id (str): ID пользователя.
        keyboard (InlineKeyboardMarkup): Список кнопок
        update_data (dict): Данные обновления от Telegram.

    Returns:
        None
    """
    max_update_id = 0
    await bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=keyboard)
    # processed_messages.append(update.message.message_id)
    while True:
        try:
            updates = await bot.get_updates(offset=max_update_id + 1, timeout=60)
            exit_flag = False
            for upd in updates:
                if upd.callback_query:
                    if upd.callback_query.message.message_id not in processed_messages:
                        processed_messages.append(upd.callback_query.message.chat.id)
                        query = upd.callback_query
                        if query.data == "add_calendar":
                            ics_file_path = os.path.join(ical_dir, ics_files[0])
                            update_data_str = json.dumps(update_data)
                            subprocess.run([PYTHON_EXE, GOOGLE_CAL, ics_file_path, update_data_str, bot_context],
                                           check=True)
                            create_users_tables_table()
                            table_name = os.path.splitext(os.path.basename(ics_file_path))[0]
                            if table_name:
                                add_user_table_entry(update.effective_user.id, table_name)
                            exit_flag = True
                            break
                        elif query.data == "get_ical_file":
                            ics_file_path = os.path.join(ical_dir, ics_files[0])
                            await bot.send_document(chat_id=user_id, document=open(ics_file_path, 'rb'))
                            # await get_ical_file(update, bot_context)
                            create_users_tables_table()
                            table_name = os.path.splitext(os.path.basename(ics_file_path))[0]
                            if table_name:
                                add_user_table_entry(update.effective_user.id, table_name)
                            exit_flag = True
                            break
            if exit_flag:
                break
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Недостаточно аргументов. Укажите update_data.")
        sys.exit(1)

    update_data = json.loads(sys.argv[1])
    update = Update.de_json(update_data, None)

    bot_context = sys.argv[2]
    user_id = sys.argv[3]
    asyncio.run(main(update, bot_context, user_id))