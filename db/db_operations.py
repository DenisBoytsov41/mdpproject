import os
import sqlite3
import json
import re
from config import DB_DIR
def connect_to_db():
    db_path = os.path.join(DB_DIR, 'schedule.db')
    return sqlite3.connect(db_path)

def normalize_table_name(file_name):
    normalized_name = re.sub(r'[^\w\s]', '', file_name)
    normalized_name = normalized_name.replace(' ', '_')
    return normalized_name
def add_schedule_to_db(schedule_data, table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week TEXT NOT NULL,
                time TEXT NOT NULL,
                week_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                classroom TEXT,
                teacher TEXT,
                lesson_type TEXT,
                group_name TEXT,
                start_time TEXT,
                end_time TEXT,
                semester INTEGER NOT NULL
            )
        ''')

        for entry in schedule_data:
            cursor.execute(f'''
                INSERT INTO {table_name} (day_of_week, time, week_type, subject, classroom, teacher, lesson_type, group_name, start_time, end_time, semester)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['День недели'],
                entry['Время'],
                entry['Тип недели'],
                entry['Название предмета'],
                entry['Аудитория'],
                entry['ФИО преподавателя'],
                entry['Тип занятия:'],
                entry['Группа'],
                entry['Начало'],
                entry['Конец'],
                entry['Семестр']
            ))

        conn.commit()
        print("Данные успешно добавлены в базу данных.")
    except sqlite3.Error as e:
        print(f"Произошла ошибка при добавлении данных в базу данных: {e}")
    finally:
        conn.close()

def load_data_from_json(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            table_name = os.path.splitext(os.path.basename(json_file_path))[0]
            table_name = normalize_table_name(table_name)
            add_schedule_to_db(data, table_name)
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден.")
    except Exception as e:
        print(f"Произошла ошибка при загрузке данных из JSON файла: {e}")

