import json
import os
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from config import THIRD_ELEMENTS_DIR
from telegram import Update
from selenium import webdriver
class NoVerifyHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLS, **pool_kwargs)

def replace_slash(input_string):
    try:
        return input_string.replace("\\/", "/").replace("_", ".")
    except Exception as e:
        print(f"Произошла ошибка при замене слэша: {e}")
        return input_string

def to_unicode_escape(input_str):
    return input_str.encode('unicode_escape').decode('utf-8')

def decode_special_chars(data):
    decoded_data_list = []
    try:
        for entry in data:
            decoded_entry = {}
            for key, value in entry.items():
                if isinstance(value, str):
                    decoded_entry[key] = value.encode('utf-8').decode('unicode_escape')
                else:
                    decoded_entry[key] = value
            decoded_data_list.append(decoded_entry)
    except Exception as e:
        print(f"Произошла ошибка при декодировании специальных символов: {e}")
    return decoded_data_list

def save_request_to_file(data_request, filename):
    filepath = os.path.join(THIRD_ELEMENTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data_request, indent=4))
    return filepath

def save_response_to_file(response, filename):
    filepath = os.path.join(THIRD_ELEMENTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(response.text)
    return filepath

def shorten_filename(filename, max_length=200):
    if len(filename) <= max_length:
        return filename
    else:
        filename, extension = os.path.splitext(filename)
        parts = filename.split("__")
        first_part = parts[0]  # schedule
        next_part = parts[1]
        last_part = parts[-1]  # группа
        truncated_name = first_part[:max_length // 2] + "__" + next_part + "__" + last_part
        return truncated_name + extension

async def send_telegram_message(update: Update, message: str):
    print(f"Отправка сообщения: {message}")

async def get_telegram_input(update: Update, prompt: str):
    response = input("Введите свой ответ: ")
    return response

def setup_driver():
    driver = webdriver.Chrome()

    return driver