import json  # Импорт модуля для работы с JSON
import os  # Импорт модуля для работы с операционной системой
import ssl  # Импорт модуля для работы с SSL
from requests.adapters import HTTPAdapter  # Импорт класса для настройки HTTP-адаптера
from urllib3.poolmanager import PoolManager  # Импорт класса для управления пулами соединений
from config import THIRD_ELEMENTS_DIR  # Импорт директории из конфигурационного файла
from telegram import Update  # Импорт класса Update из модуля telegram
from selenium import webdriver  # Импорт модуля для автоматизации браузера
class NoVerifyHTTPAdapter(HTTPAdapter):  # Определение нового класса, наследующего HTTPAdapter
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):  # Определение метода для инициализации менеджера пулов
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,  # Создание экземпляра PoolManager с указанными параметрами
                                       ssl_version=ssl.PROTOCOL_TLS, **pool_kwargs)

def replace_slash(input_string):  # Определение функции для замены символов
    try:  # Обработка возможных ошибок
        return input_string.replace("\\/", "/").replace("_", ".")  # Замена символов "\" на "/", а также замена символов "_" на "."
    except Exception as e:  # Обработка исключений
        print(f"Произошла ошибка при замене слэша: {e}")  # Вывод сообщения об ошибке
        return input_string  # Возврат исходной строки в случае ошибки

def to_unicode_escape(input_str):  # Определение функции для преобразования строки в формат Unicode escape
    return input_str.encode('unicode_escape').decode('utf-8')  # Преобразование строки в формат Unicode escape и возврат результата

def decode_special_chars(data):  # Определение функции для декодирования специальных символов
    decoded_data_list = []  # Инициализация пустого списка для хранения декодированных данных
    try:  # Обработка возможных ошибок
        for entry in data:  # Перебор элементов входных данных
            decoded_entry = {}  # Инициализация пустого словаря для хранения декодированной записи
            for key, value in entry.items():  # Перебор элементов словаря
                if isinstance(value, str):  # Проверка, является ли значение строкой
                    decoded_entry[key] = value.encode('utf-8').decode('unicode_escape')  # Декодирование специальных символов в значении
                else:
                    decoded_entry[key] = value  # Присвоение значения без декодирования
            decoded_data_list.append(decoded_entry)  # Добавление декодированной записи в список
    except Exception as e:  # Обработка исключений
        print(f"Произошла ошибка при декодировании специальных символов: {e}")  # Вывод сообщения об ошибке
    return decoded_data_list  # Возврат списка с декодированными данными

def save_request_to_file(data_request, filename):  # Определение функции для сохранения запроса в файл
    filepath = os.path.join(THIRD_ELEMENTS_DIR, filename)  # Формирование пути к файлу
    with open(filepath, "w", encoding="utf-8") as file:  # Открытие файла для записи
        file.write(json.dumps(data_request, indent=4))  # Запись запроса в файл в формате JSON с отступами
    return filepath  # Возврат пути к сохраненному файлу

def save_response_to_file(response, filename):  # Определение функции для сохранения ответа в файл
    filepath = os.path.join(THIRD_ELEMENTS_DIR, filename)  # Формирование пути к файлу
    with open(filepath, "w", encoding="utf-8") as file:  # Открытие файла для записи
        file.write(response.text)  # Запись текста ответа в файл
    return filepath  # Возврат пути к сохраненному файлу

def shorten_filename(filename, max_length=200):  # Определение функции для сокращения имени файла
    if len(filename) <= max_length:  # Проверка, не превышает ли длина имени максимально допустимое значение
        return filename  # Возврат исходного имени файла
    else:
        filename, extension = os.path.splitext(filename)  # Разделение имени файла и расширения
        parts = filename.split("__")  # Разделение имени на части по разделителю "__"
        first_part = parts[0]  # Получение первой части имени
        next_part = parts[1]  # Получение второй части имени
        last_part = parts[-1]  # Получение последней части имени
        truncated_name = first_part[:max_length // 2] + "__" + next_part + "__" + last_part  # Формирование сокращенного имени
        return truncated_name + extension  # Возврат сокращенного имени с расширением

async def send_telegram_message(update: Update, message: str):  # Определение асинхронной функции для отправки сообщения в Telegram
    print(f"Отправка сообщения: {message}")  # Вывод сообщения об отправке сообщения

async def get_telegram_input(update: Update, prompt: str):  # Определение асинхронной функции для получения ввода от пользователя в Telegram
    response = input("Введите свой ответ: ")  # Запрос ввода от пользователя в консоли
    return response  # Возврат введенного пользователем ответа

def setup_driver():  # Определение функции для настройки драйвер
    driver = webdriver.Chrome()  # Создание экземпляра веб-драйвера Chrome
    return driver  # Возврат созданного драйвера