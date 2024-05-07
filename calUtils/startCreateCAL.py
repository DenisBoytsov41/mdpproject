import json
import locale
import sys
import os.path
from calendar_utils import create_icalendar, create_event
from db.db_operations import extract_data_format1_from_db, extract_data_format2_from_db

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

def extract_data_from_db(output_json_file):
    table_name = os.path.splitext(os.path.basename(output_json_file))[0]
    if "schedule_4_" in table_name or "schedule_3_" in table_name:
        return extract_data_format1_from_db(table_name)
    else:
        return extract_data_format2_from_db(table_name)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Недостаточно аргументов. Укажите output_json_file.")
        sys.exit(1)

    output_json_file = sys.argv[1]
    try:
        with open(output_json_file, 'r', encoding='utf-8') as file:
            schedule_json = file.read()
            data = json.loads(schedule_json)
    except FileNotFoundError:
        print(f"Файл {output_json_file} не найден. Извлечение данных из БД.")
        data = extract_data_from_db(output_json_file)

    create_icalendar(data, output_json_file)
