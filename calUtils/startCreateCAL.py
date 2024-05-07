import json
import locale
import sys
import os.path
from calendar_utils import create_icalendar, create_event
from db.db_operations import extract_data_format1_from_db, extract_data_format2_from_db

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

def extract_data_from_db(output_json_file):
    # Извлекаем название таблицы из пути к файлу JSON
    table_name = os.path.splitext(os.path.basename(output_json_file))[0]
    if "schedule_4_" in table_name or "schedule_3_" in table_name:
        return extract_data_format1_from_db(table_name)
    else:
        return extract_data_format2_from_db(table_name)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Недостаточно аргументов. Укажите output_json_file и schedule_json.")
        sys.exit(1)

    output_json_file = sys.argv[1]
    #schedule_json = sys.argv[2]
    schedule_json = None

    if schedule_json:
        data = json.loads(schedule_json)
    else:
        data = extract_data_from_db(output_json_file)

    create_icalendar(data, output_json_file)
