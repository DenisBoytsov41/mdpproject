import json
import os
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from config import THIRD_ELEMENTS_DIR
class NoVerifyHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLS, **pool_kwargs)

def replace_slash(input_string):
    try:
        return input_string.replace("\\/", "/")
    except Exception as e:
        print(f"Произошла ошибка при замене слэша: {e}")
        return input_string

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