import sqlite3

def create_table():
    try:
        conn = sqlite3.connect('schedule.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Schedule (
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
        print("Таблица успешно создана")
        conn.close()
    except sqlite3.Error as err:
        print(f"Ошибка при создании таблицы: {err}")

if __name__ == "__main__":
    create_table()
