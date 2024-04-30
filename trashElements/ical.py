from tkinter import filedialog
from tkinter import Tk
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import requests
import json
from copy import deepcopy

def fetch_schedule_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Failed to fetch data. Status code: {response.status_code}")

def get_current_semester_start():
    today = datetime.today()
    if today.month < 2 or (today.month == 2 and today.day < 5):
        # Весенний семестр
        start_date = datetime(today.year, 2, 5)
    else:
        # Осенний семестр
        start_date = datetime(today.year, 9, 1)

    # Проверяем, чтобы начальная дата не была в воскресенье
    while start_date.weekday() == 6:
        start_date += timedelta(days=1)

    return start_date

def create_icalendar(data):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')

    # Дата начала семестра
    start_date = get_current_semester_start()

    # Определяем дату окончания семестра
    if start_date.month < 2 or (start_date.month == 2 and start_date.day < 5):
        # Осенний семестр заканчивается 30 декабря
        end_date = datetime(start_date.year, 12, 30)
    else:
        # Весенний семестр заканчивается 30 июня
        end_date = datetime(start_date.year, 6, 30)

    # Проходим по всем записям и создаем события для каждого дня семестра
    while start_date <= end_date:
        # Пропускаем воскресенье
        if start_date.weekday() == 6:
            start_date += timedelta(days=1)
            continue

        for entry in data:
            # Пропускаем воскресенье
            if entry["День недели"] == "Воскресенье":
                continue

            event = Event()
            event.add('description',
                      f'{entry["Тип занятия:"]} ({entry["Тип недели"]})\nПреподаватель: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')

            start_time_str, end_time_str = entry["Время"].split(" - ")
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")

            # Создаем событие для обеих недель
            for week_type in ["Над чертой", "Под чертой"]:
                week_event = deepcopy(event)  # Вместо clone используем deepcopy
                week_event.add('dtstart', start_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
                week_event.add('dtend', start_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
                week_event.add('summary', f'{entry["Название предмета"]} ({week_type})')
                week_event.add('location', entry["Аудитория"])
                cal.add_component(week_event)

        start_date += timedelta(days=1)

    # Сохраняем в файл
    file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])
    if file_path:
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())

if __name__ == "__main__":
    # Загружаем данные из JSON файла
    Tk().withdraw()  # Отключаем основное окно Tkinter
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

    if file_path:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Создаем iCalendar
        create_icalendar(data)
