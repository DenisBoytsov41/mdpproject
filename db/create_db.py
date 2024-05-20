import sqlite3  # Импортируем модуль для работы с SQLite базами данных

def create_table(): # Объявляем функцию для создания таблицы
    try:  # Используем конструкцию try-except для обработки возможных ошибок
        conn = sqlite3.connect(
            'schedule.db')  # Устанавливаем соединение с базой данных 'schedule.db' или создаем ее, если она не существует
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
        ''')  # Запрос на создание таблицы с указанными полями
        print("Таблица успешно создана")  # Выводим сообщение об успешном создании таблицы
        conn.close()  # Закрываем соединение с базой данных
    except sqlite3.Error as err:  # Обрабатываем ошибки SQLite
        print(f"Ошибка при создании таблицы: {err}")  # Выводим сообщение об ошибке

if __name__ == "__main__":  # Проверяем, что скрипт запущен как основная программа
    create_table()  # Вызываем функцию создания таблицы
