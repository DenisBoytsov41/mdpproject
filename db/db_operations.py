import os
import sqlite3
import json
import re
import sys
from config import DB_DIR

# Функция для подключения к базе данных SQLite
def connect_to_db():
    db_path = os.path.join(DB_DIR, 'schedule.db')
    return sqlite3.connect(db_path)

# Функция для создания таблицы users_tables в базе данных
def create_users_tables_table():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_tables'")
        existing_table = cursor.fetchone()

        if not existing_table:
            # Если таблицы нет, создаем её
            cursor.execute('''
                CREATE TABLE users_tables (
                    user_id INTEGER PRIMARY KEY,
                    table_names TEXT
                )
            ''')

        conn.commit()
        print("Таблица users_tables успешно создана.")
    except Exception as e:
        print(f"Произошла ошибка при создании таблицы users_tables: {e}")
    finally:
        conn.close()

# Функция для удаления таблицы users_tables из базы данных
def drop_users_tables_table():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_tables'")
        existing_table = cursor.fetchone()

        if existing_table:
            cursor.execute('''DROP TABLE users_tables''')
            conn.commit()
            print("Таблица users_tables успешно удалена.")
        else:
            print("Таблицы users_tables не существует.")
    except Exception as e:
        print(f"Произошла ошибка при удалении таблицы users_tables: {e}")
    finally:
        conn.close()

# Функция для добавления записи о таблице пользователя в таблицу users_tables
def add_user_table_entry(user_id, table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Получаем текущие названия таблиц для данного пользователя
        cursor.execute("SELECT table_names FROM users_tables WHERE user_id=?", (user_id,))
        user_tables_entry = cursor.fetchone()

        if user_tables_entry:
            current_table_names = user_tables_entry[0].split(',')
            if table_name not in current_table_names:
                current_table_names.append(table_name)
                updated_table_names = ','.join(current_table_names)
                cursor.execute("UPDATE users_tables SET table_names=? WHERE user_id=?", (updated_table_names, user_id))
                print(f"Добавлено новое название таблицы для пользователя {user_id}: {table_name}")
            else:
                print(f"Название таблицы {table_name} уже существует для пользователя {user_id}")
        else:
            # Если записи о пользователе нет, создаем новую
            cursor.execute("INSERT INTO users_tables (user_id, table_names) VALUES (?, ?)", (user_id, table_name))
            print(f"Добавлена новая запись в таблицу users_tables: user_id={user_id}, table_name={table_name}")

        conn.commit()
    except Exception as e:
        print(f"Произошла ошибка при добавлении записи в таблицу users_tables: {e}")
    finally:
        conn.close()

# Функция для получения списка файлов .ics для указанного пользователя
def get_user_ics_files(user_id):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("SELECT table_names FROM users_tables WHERE user_id=?", (user_id,))
        user_tables_entry = cursor.fetchone()

        if user_tables_entry:
            table_names = user_tables_entry[0]
            ics_files = table_names.split(',')
            return [f"{table_name}.ics" for table_name in ics_files]
        else:
            return []
    except Exception as e:
        print(f"Произошла ошибка при получении файлов .ics для пользователя {user_id}: {e}")
        return []
    finally:
        conn.close()

# Функция для нормализации параметра
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

# Функция для нормализации названия файла
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

# Функция для добавления расписания в базу данных
def add_schedule_to_db(schedule_data, table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        existing_table = cursor.fetchone()

        if not existing_table:
            # Если таблицы нет, создаем её
            cursor.execute(f'''
                CREATE TABLE {table_name} (
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

        for idx, entry in enumerate(schedule_data, start=1):
            # Вставляем данные с указанием id
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
                REPLACE INTO {table_name} (id, day_of_week, date, time, week_type, subject, classroom, teacher, lesson_type, group_name, start_time, end_time, semester, file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                idx, day_of_week, date, time, week_type, subject, classroom, teacher, lesson_type, group_name, start_time, end_time, semester, file
            ))

        conn.commit()
        print("Данные успешно добавлены в базу данных.")
    except sqlite3.Error as e:
        print(f"Произошла ошибка при добавлении данных в базу данных: {e}")
    finally:
        conn.close()

# Функция для загрузки данных из JSON файла в базу данных
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

# Функция для извлечения данных формата 1 из базы данных
def extract_data_format1_from_db(table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM {table_name}
        ''')

        data = []
        for row in cursor.fetchall():
            entry = {
                "День недели": row[1],
                "Время": row[3],
                "Тип недели": row[4],
                "Название предмета": row[5],
                "Аудитория": row[6],
                "ФИО преподавателя": row[7],
                "Тип занятия": row[8],
                "Группа": row[9],
                "Начало": row[10],
                "Конец": row[11],
                "Семестр": row[12],
                "Файл": row[13]
            }
            data.append(entry)

            return data
    except sqlite3.Error as e:
        print(f"Произошла ошибка при извлечении данных из БД: {e}")
        return None
    finally:
        conn.close()

# Функция для извлечения данных формата 2 из базы данных
def extract_data_format2_from_db(table_name):
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM {table_name}
        ''')

        data = []
        for row in cursor.fetchall():
            entry = {
                "День недели": row[1],
                "Дата": row[2],
                "Время": row[3],
                "Название предмета": row[5],
                "Группа": row[9],
                "Аудитория": row[6],
                "Тип занятия": row[8],
                "Семестр": row[12],
                "Файл": row[13]
            }
            data.append(entry)

        return data
    except sqlite3.Error as e:
        print(f"Произошла ошибка при извлечении данных из БД: {e}")
        return None
    finally:
        conn.close()

def convert_data_to_json(data):
    try:
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        return json_data
    except Exception as e:
        print(f"Произошла ошибка при преобразовании данных в JSON: {e}")
        return None

