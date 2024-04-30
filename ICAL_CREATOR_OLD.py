from datetime import datetime, timedelta
from tkinter import filedialog
from tkinter import Tk
from icalendar import Calendar, Event
import json
import locale
import calendar
from icalendar import vRecur

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

def get_current_week_type(start_date, current_date=None):
    if current_date is None:
        current_date = get_current_semester_start()

    # Находим ближайший понедельник или текущий понедельник, если start_date - это понедельник
    while start_date.weekday() != 0:
        start_date -= timedelta(days=1)

    weeks_passed = abs(current_date - start_date).days // 7
    print(current_date)
    print(start_date)
    print(weeks_passed)

    return "Под чертой" if weeks_passed % 2 == 0 or weeks_passed == 0 else "Над чертой"

def get_current_semester_start():
    today = datetime.today()
    if today.month <= 8:
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
    print(start_date)
    print(end_date)

    # Проходим по всем дням недели
    current_date = get_current_semester_start()
    days_to_process = 6  # Количество дней, которые мы хотим обработать

    while current_date <= get_current_semester_end() and days_to_process > 0:
        # Пропускаем воскресенье
        if current_date.weekday() == 6:
            current_date += timedelta(days=1)
            continue

        # Проходим по всем записям и создаем события с повторением для текущего дня недели
        for entry in data:
            # Пропускаем записи, не соответствующие текущему дню недели
            if entry["День недели"].lower() != current_date.strftime("%A").lower():
                continue

            event = Event()
            event.add('description',
                      f'{entry["Тип занятия:"]} \nПреподаватель/Группа: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')

            start_time_str, end_time_str = entry["Время"].split(" - ")
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")

            # Создаем правило повторения события
            rule = vRecur(freq='weekly', until=get_current_semester_end())
            event.add('rrule', rule)

            # Добавляем время начала и окончания события
            event.add('dtstart', current_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
            event.add('dtend', current_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
            event.add('summary', f'{entry["Название предмета"]} ({get_current_week_type(current_date)})')
            event.add('location', entry["Аудитория"])
            cal.add_component(event)

        current_date += timedelta(days=1)
        days_to_process -= 1

    # Сохраняем в файл
    file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])
    if file_path:
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())

if __name__ == "__main__":
    Tk().withdraw()  # Отключаем основное окно Tkinter
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

    if file_path:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Создаем iCalendar с событиями с повторением
        create_icalendar(data)