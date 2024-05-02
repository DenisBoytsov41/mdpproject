import json
from datetime import datetime, timedelta
from tkinter import filedialog
from icalendar import Calendar, Event
from icalendar import vRecur
from semester_utils import get_current_week_type, get_current_semester_start, get_current_semester_end, adjust_dates_based_on_week_type
from APIelements.holiday_or_weekend import extract_holidays


def create_icalendar(data):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')

    url = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"
    holidays_response = extract_holidays(url)
    holidays_json = json.loads(holidays_response)

    semester_start = get_current_semester_start()
    semester_end = get_current_semester_end()

    semester_holidays = {}
    for holiday in holidays_json:
        holiday_date = datetime.strptime(holiday['date'], "%Y-%m-%d")
        if semester_start <= holiday_date <= semester_end:
            semester_holidays[holiday_date] = holiday_date

    for entry in data:
        if entry.get("Семестр") in [2, 3]:
            start_date_str = entry.get("Начало")
            end_date_str = entry.get("Конец")
            week_type = entry.get("Тип недели")

            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
                type_weekStart = get_current_week_type(start_date)
                holiday_used = False
                flag_data = start_date + timedelta(days=7)

                while flag_data < end_date:
                    end_d = start_date
                    for holiday_date in semester_holidays:
                        if end_d == holiday_date:
                            create_event(cal, entry, start_date, start_date, week_type, holiday_date, entry.get("Семестр"))
                            holiday_used = True
                        start_date, end_d = adjust_dates_based_on_week_type(start_date, end_d, type_weekStart,
                                                                               week_type)
                        type_weekStart = get_current_week_type(start_date)
                        flag_data += timedelta(days=7)

                if not holiday_used:
                    create_event(cal, entry, start_date, start_date, week_type, end_date, entry.get("Семестр"))

            else:
                current_date = semester_start
                end_semester = get_current_semester_end()
                while current_date <= end_semester:
                    if current_date.strftime("%A").lower() == entry.get("День недели").lower():
                        type_weekStart = get_current_week_type(current_date)
                        holiday_used = False
                        flag_data = current_date + timedelta(days=7)
                        start_date = current_date

                        while flag_data < end_semester:
                            end_date = start_date
                            for holiday_date in semester_holidays:
                                if end_date == holiday_date:
                                    create_event(cal, entry, start_date, start_date, week_type, holiday_date,
                                                 entry.get("Семестр"))
                                    holiday_used = True
                                start_date, end_date = adjust_dates_based_on_week_type(start_date, end_date,
                                                                                    type_weekStart,
                                                                                    week_type)
                                type_weekStart = get_current_week_type(start_date)
                                flag_data += timedelta(days=7)

                        if not holiday_used:
                            create_event(cal, entry, start_date, start_date, week_type, end_semester, entry.get("Семестр"))
                        break
                    current_date += timedelta(days=1)
        else:
            start_date_str = entry.get("Дата")
            start_date = datetime.strptime(start_date_str, "%Y.%m.%d")
            end_date = get_current_semester_end()
            holiday_used = False
            for holiday_date in semester_holidays:
                if end_date > holiday_date:
                    create_event(cal, entry, start_date, start_date, None, holiday_date,
                                 entry.get("Семестр"))
                    start_date = holiday_date + timedelta(days=1)
                    holiday_used = True

            if not holiday_used:
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

    if week_type is None and end_semester is not None:
        end_date = end_semester + timedelta(days=1)

    event.add('dtstart', start_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
    event.add('dtend', end_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
    event.add('summary', f'{entry["Название предмета"]} ({week_type})' if week_type else entry["Название предмета"])
    event.add('location', entry["Аудитория"])

    cal.add_component(event)
