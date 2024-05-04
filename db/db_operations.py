import os
import sqlite3
import json
import re
import sys
from config import DB_DIR
def connect_to_db():
    db_path = os.path.join(DB_DIR, 'schedule.db')
    return sqlite3.connect(db_path)
def normalize_parameter(param):
    try:
        current_encoding = getattr(param, 'encoding', None)
        if current_encoding is None or current_encoding.lower() != 'utf-8':
            decoded_param = param.encode('utf-8').decode('unicode-escape')
        else:
            decoded_param = param

        return decoded_param
    except Exception as e:
        print(f"Произошла ошибка при нормализации параметра: {e}")
        return None

def normalize_table_name(file_name):
    try:
        words = re.findall(r'\w+', file_name)
        normalized_name = '_'.join(words)
        encoded_name = normalized_name.encode('utf-8')
        decoded_name = encoded_name.decode('utf-8')
        return decoded_name
    except Exception as e:
        print(f"Произошла ошибка при нормализации названия файла: {e}")
        return None



def add_schedule_to_db(schedule_data, table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week TEXT NOT NULL,
                date TEXT,
                time TEXT NOT NULL,
                week_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                classroom TEXT,
                teacher TEXT,
                lesson_type TEXT,
                group_name TEXT,
                start_time TEXT,
                end_time TEXT,
                semester INTEGER NOT NULL,
                file TEXT
            )
        ''')

        for entry in schedule_data:
            # Проверка наличия ключей в записи расписания
            day_of_week = entry.get('День недели', '')
            date = entry.get('Дата', '')
            time = entry.get('Время', '')
            week_type = entry.get('Тип недели', '')
            subject = entry.get('Название предмета', '')
            classroom = entry.get('Аудитория', '')
            teacher = entry.get('ФИО преподавателя', '')
            lesson_type = entry.get('Тип занятия', '')
            group_name = entry.get('Группа', '')
            start_time = entry.get('Начало', '')
            end_time = entry.get('Конец', '')
            semester = entry.get('Семестр', '')
            file = entry.get('Файл', '')

            cursor.execute(f'''
                INSERT INTO {table_name} (day_of_week, date, time, week_type, subject, classroom, teacher, lesson_type, group_name, start_time, end_time, semester, file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                day_of_week, date, time, week_type, subject, classroom, teacher, lesson_type, group_name, start_time, end_time, semester, file
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

