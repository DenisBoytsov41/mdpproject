import requests


def search_kgu_corps():
    url = "https://yandex.ru/search/"
    params = {
        "text": "корпуса КГУ Кострома",
        "lr": "213",  # Код региона (213 для Костромской области)
        "numdoc": "10"  # Количество результатов на странице
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        # Вывести результаты
        print(response.text)
    else:
        print("Error:", response.status_code)


if __name__ == "__main__":
    search_kgu_corps()
