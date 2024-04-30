import json

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        print("Файл не найден!")
        return None
    except json.JSONDecodeError:
        print("Ошибка при чтении JSON файла!")
        return None