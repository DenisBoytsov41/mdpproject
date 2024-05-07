from datetime import datetime, timedelta
from tkinter import filedialog
from tkinter import Tk
from icalendar import Calendar, Event
import json
import locale
import calendar

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
def get_current_week_type(start_date, current_date=None):
    if current_date is None:
        current_date = datetime.now()

    # Находим ближайший понедельник или текущий понедельник, если start_date - это понедельник
    while start_date.weekday() != 0:
        start_date -= timedelta(days=1)

    weeks_passed = (current_date - start_date).days // 7
    return "Под чертой" if weeks_passed % 2 == 0 else "Над чертой"

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

def get_current_semester_end():
    start_date = get_current_semester_start()
    if start_date.month < 2 or (start_date.month == 2 and start_date.day < 5):
        # Осенний семестр заканчивается 30 декабря
        end_date = datetime(start_date.year, 12, 30)
    else:
        # Весенний семестр заканчивается 30 июня
        end_date = datetime(start_date.year, 6, 30)

    return end_date

def create_icalendar(data):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')

    # Дата начала и окончания семестра
    start_date = get_current_semester_start()
    end_date = get_current_semester_end()

    # Проходим по всем записям и создаем события для каждого дня семестра
    while start_date <= end_date:
        # Пропускаем воскресенье
        if start_date.weekday() == 6:
            start_date += timedelta(days=1)
            continue
        day_entries = [entry for entry in data if entry["День недели"].lower() == start_date.strftime("%A")]
        print(data)
        print("------------")
        print("------------")
        print(day_entries)
        print("------------")
        for entry in day_entries:
            # Пропускаем воскресенье
            if entry["День недели"].lower() == "воскресенье":
                continue

            event = Event()
            event.add('description',
                      f'{entry["Тип занятия:"]} \nПреподаватель: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')

            start_time_str, end_time_str = entry["Время"].split(" - ")
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")

            # Переменная для хранения типа недели предмета
            entry_week_type = entry["Тип недели"].lower()

            # Создаем событие только для текущего типа недели
            if entry_week_type == "общая" or entry_week_type == get_current_week_type(start_date).lower():
                week_event = Event()
                week_event.add('description', event.decoded('description'))
                week_event.add('dtstart', start_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
                week_event.add('dtend', start_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
                week_event.add('summary', f'{entry["Название предмета"]} ({get_current_week_type(start_date)})')
                week_event.add('location', entry["Аудитория"])
                cal.add_component(week_event)

        start_date += timedelta(days=1)

    # Сохраняем в файл
    file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])
    if file_path:
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())

if __name__ == "__main__":
    Tk().withdraw()  # Отключаем основное окно Tkinter
    file_path = filedialog.askopenfilename(filetypes=[("jsonAndIcal files", "*.json")])

    if file_path:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Создаем iCalendar

        create_icalendar(data)
