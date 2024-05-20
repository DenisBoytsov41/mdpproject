import json  # Импорт модуля json для работы с JSON-файлами.

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:  # Открытие JSON-файла для чтения в кодировке utf-8.
            data = json.load(json_file)  # Загрузка данных из JSON-файла в переменную data.
        return data  # Возвращает данные из JSON-файла.
    except FileNotFoundError:  # Обработка исключения, если файл не найден.
        print("Файл не найден!")  # Вывод сообщения об ошибке.
        return None  # Возвращает None.
    except json.JSONDecodeError:  # Обработка исключения, если произошла ошибка при декодировании JSON.
        print("Ошибка при чтении jsonAndIcal файла!")  # Вывод сообщения об ошибке.
        return None  # Возвращает None.
