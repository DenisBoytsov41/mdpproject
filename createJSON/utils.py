import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
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