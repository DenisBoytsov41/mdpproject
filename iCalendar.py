from datetime import datetime, timedelta
from icalendar import Calendar, Event
from tkinter import filedialog
from tkinter import Tk
import json


def create_icalendar(data):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')

    # Дата начала семестра
    start_date = get_current_semester_start()

    # Проходим по всем записям и создаем события для каждого занятия
    for entry in data:
        # Пропускаем записи, где не указано начало и конец
        if not entry["Начало"] or not entry["Конец"]:
            continue

        # Пропускаем воскресенье
        if entry["День недели"] == "Воскресенье":
            continue

        # Пропускаем занятия, которые еще не начались
        start_date_entry = datetime.strptime(entry["Начало"], "%d.%m.%Y")
        if start_date_entry > datetime.now():
            continue

        # Пропускаем занятия, которые уже закончились
        end_date_entry = datetime.strptime(entry["Конец"], "%d.%m.%Y")
        if end_date_entry < datetime.now():
            continue

        # Пропускаем занятия в дни недели, которые уже прошли
        while start_date_entry.weekday() == 6:
            start_date_entry += timedelta(days=1)
        if start_date_entry.weekday() != get_current_weekday():
            continue

        event = Event()
        event.add('description',
                  f'{entry["Тип занятия:"]} ({entry["Тип недели"]})\nПреподаватель: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')

        start_time_str, end_time_str = entry["Время"].split(" - ")
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")

        # Создаем событие для обеих недель, если тип недели "Общая"
        if entry["Тип недели"] == "Общая":
            week_type = get_current_week_type(start_date)
            start_datetime_nad_chertoy = start_date_entry + timedelta(hours=start_time.hour, minutes=start_time.minute)
            end_datetime_nad_chertoy = start_date_entry + timedelta(hours=end_time.hour, minutes=end_time.minute)

            event_nad_chertoy = Event()
            event_nad_chertoy.add('dtstart', start_datetime_nad_chertoy)
            event_nad_chertoy.add('dtend', end_datetime_nad_chertoy)
            event_nad_chertoy.add('summary', f'{entry["Название предмета"]} (Над чертой)')
            event_nad_chertoy.add('location', entry["Аудитория"])
            event_nad_chertoy.add('description',
                                  f'{entry["Тип занятия:"]} (Общая)\nПреподаватель: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')
            cal.add_component(event_nad_chertoy)

            # Теперь создаем событие для "Под чертой"
            week_type = "Под чертой" if week_type == "Над чертой" else "Над чертой"
            start_datetime_pod_chertoy = start_date_entry + timedelta(hours=start_time.hour, minutes=start_time.minute)
            end_datetime_pod_chertoy = start_date_entry + timedelta(hours=end_time.hour, minutes=end_time.minute)

            event_pod_chertoy = event_nad_chertoy.clone()
            event_pod_chertoy.add('dtstart', start_datetime_pod_chertoy)
            event_pod_chertoy.add('dtend', end_datetime_pod_chertoy)
            event_pod_chertoy.add('summary', f'{entry["Название предмета"]} (Под чертой)')
            cal.add_component(event_pod_chertoy)

    # Сохраняем в файл
    file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])
    if file_path:
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())


# Функция для получения текущего дня недели (0 - понедельник, 1 - вторник, и так далее)
def get_current_weekday():
    return (datetime.now().weekday() + 1) % 7


def get_current_week_type(start_date, current_date=None):
    if current_date is None:
        current_date = datetime.now()
    weeks_passed = (current_date - start_date).days // 7
    return ["Под чертой", "Над чертой"] if weeks_passed % 2 == 0 else ["Над чертой", "Под чертой"]


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


if __name__ == "__main__":
    Tk().withdraw()  # Отключаем основное окно Tkinter
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

    if file_path:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Создаем iCalendar
        create_icalendar(data)
