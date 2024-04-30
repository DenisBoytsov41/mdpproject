from datetime import datetime, timedelta
from tkinter import filedialog
from icalendar import Calendar, Event
from icalendar import vRecur
from semester_utils import get_current_week_type, get_current_semester_start, get_current_semester_end

def create_icalendar(data):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')

    for entry in data:
        if entry.get("Семестр") in [2, 3]:
            start_date_str = entry.get("Начало")
            end_date_str = entry.get("Конец")
            week_type = entry.get("Тип недели")

            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
                create_event(cal, entry, start_date, start_date, week_type, end_date, entry.get("Семестр"))
            else:
                current_date = get_current_semester_start()
                end_semester = get_current_semester_end()
                while current_date <= end_semester:
                    if current_date.strftime("%A").lower() == entry.get("День недели").lower():
                        create_event(cal, entry, current_date, current_date, week_type, end_semester,entry.get("Семестр"))
                        break
                    current_date += timedelta(days=1)
        else:
            start_date_str = entry.get("Дата")
            start_date = datetime.strptime(start_date_str, "%Y.%m.%d")
            create_event(cal, entry, start_date, start_date, None, None, entry.get("Семестр"))

    file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])
    if file_path:
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())


def create_event(cal, entry, start_date, end_date, week_type, end_semester, semester):
    event = Event()
    if semester != 2 and semester != 3:
        event.add('description',
                  f'{entry["Тип занятия"]} \nПреподаватель/Группа: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')
    else:
        event.add('description',
                  f'{entry["Тип занятия:"]} \nПреподаватель/Группа: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}')


    start_time_str, end_time_str = entry["Время"].split(" - ")
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")

    if week_type is not None:
        rule = vRecur(freq='weekly')
        if week_type == "Под чертой" or week_type == "Над чертой":
            rule['interval'] = 2
        else:
            rule['interval'] = 1

        if week_type == "Над чертой":
            start_date += timedelta(days=7)
            end_date += timedelta(days=7)

        rule['until'] = end_semester + timedelta(days=1)  # Устанавливаем дату окончания

        event.add('rrule', rule)

    event.add('dtstart', start_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
    event.add('dtend', end_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
    event.add('summary', f'{entry["Название предмета"]} ({week_type})' if week_type else entry["Название предмета"])
    event.add('location', entry["Аудитория"])

    cal.add_component(event)



