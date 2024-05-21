import json  # Импорт модуля json для работы с JSON-данными.
import locale  # Импорт модуля locale для работы с локальными настройками.
import sys  # Импорт модуля sys для работы с системными параметрами и функциями.
import os.path  # Импорт модуля os.path для работы с путями к файлам.
from calendar_utils import create_icalendar  # Импорт функций из модуля calendar_utils.
from allClasses.ICalendarCreator import CalendarCreator
from db.db_operations import extract_data_format1_from_db, extract_data_format2_from_db  # Импорт функций из модуля db_operations.

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')  # Установка локали на русскую.

def extract_data_from_db(output_json_file):
    """Функция извлекает данные из базы данных в зависимости от имени таблицы и формата."""
    table_name = os.path.splitext(os.path.basename(output_json_file))[0]  # Извлекаем имя таблицы из имени файла.
    if "schedule_4_" in table_name or "schedule_3_" in table_name:  # Если имя таблицы соответствует формату 1.
        return extract_data_format1_from_db(table_name)  # Извлекаем данные из базы данных формата 1.
    else:  # Иначе, если имя таблицы соответствует формату 2.
        return extract_data_format2_from_db(table_name)  # Извлекаем данные из базы данных формата 2.

if __name__ == "__main__":  # Проверяем, что скрипт запущен напрямую, а не импортирован в другой модуль.
    if len(sys.argv) < 2:  # Если количество аргументов меньше 2 (отсутствует output_json_file).
        print("Недостаточно аргументов. Укажите output_json_file.")  # Выводим сообщение об ошибке.
        sys.exit(1)  # Выходим из программы с кодом ошибки 1.

    output_json_file = sys.argv[1]  # Получаем имя выходного JSON-файла из аргументов командной строки.
    try:
        with open(output_json_file, 'r', encoding='utf-8') as file:  # Пытаемся открыть JSON-файл на чтение.
            schedule_json = file.read()  # Читаем содержимое файла.
            data = json.loads(schedule_json)  # Преобразуем JSON-строку в объект Python.
    except FileNotFoundError:  # Если файл не найден.
        print(f"Файл {output_json_file} не найден. Извлечение данных из БД.")  # Выводим сообщение.
        data = extract_data_from_db(output_json_file)  # Извлекаем данные из базы данных.

    #calendar_url  = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"
    #manager = CalendarCreator()
    #manager.create_icalendar(data, output_json_file)
    #create_icalendar(data, output_json_file)  # Создаем iCalendar и сохраняем в файл.
    create_icalendar(data, output_json_file)