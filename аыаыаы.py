import hashlib


def get_hash_from_cookie(cookie_value, hexMass):
    # Получаем индекс алгоритма хэширования из значения cookie
    algorithm_index = int(cookie_value)

    # Получаем название алгоритма хэширования из списка hexMass
    algorithm_name = hexMass[algorithm_index]

    # Создаем объект хэширования с использованием выбранного алгоритма
    hash_object = getattr(hashlib, algorithm_name)()

    # Обновляем хэш, добавляя данные 'true'
    hash_object.update(b'true')

    # Получаем строковое представление хэша в шестнадцатеричном формате
    hex_digest = hash_object.hexdigest()

    return hex_digest


# Пример использования:
hexMass = ["sha1", "sha256", "md5"]  # Список алгоритмов хэширования

# Предположим, что значение cookie '_help_yandex_2' равно 1 (индекс алгоритма "sha256")
cookie_value = "1"
hash_value = get_hash_from_cookie(cookie_value, hexMass)
print("Хэш, полученный из cookie:", hash_value)
