import json
from datetime import datetime, timedelta
from tkinter import filedialog
from icalendar import Calendar, Event
from icalendar import vRecur
from semester_utils import (get_current_week_type, get_current_semester_start,
                            get_current_semester_end, adjust_dates_based_on_week_type, save_calendar, add_semester_holidays)
from APIelements.holiday_or_weekend import extract_holidays
from allClasses.EventCreator import EventCreator

def create_icalendar(data,output_json_file = None):
    cal = Calendar()
    cal.add('prodid', '-//KSU//RU')
    cal.add('version', '2.0')
    holidays_json = fetch_holidays()

    semester_start = get_current_semester_start()
    semester_end = get_current_semester_end()
    semester_holidays = add_semester_holidays(holidays_json, semester_start, semester_end)

    for entry in data:
        if entry.get("Семестр") in [2, 3]:
            start_date_str = entry.get("Начало")
            end_date_str = entry.get("Конец")
            week_type = entry.get("Тип недели")

            if start_date_str and end_date_str:
                process_event_dates(cal, entry, start_date_str,end_date_str, week_type, semester_holidays)
            else:
                process_weekly_schedule(cal, entry, semester_start,semester_holidays, week_type)
        else:
            start_date_str, start_date = create_single_day_event(cal,entry)
    save_calendar(cal, output_json_file)

def fetch_holidays():
    url = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"
    holidays_response = extract_holidays(url)
    return json.loads(holidays_response)

def collect_holiday_dates(start_date, end_date, type_weekStart, week_type, semester_holidays):
    holiday_dates = []
    start_date_vrem = start_date
    end_date_vrem = start_date
    while start_date_vrem <= end_date:
        end_date_vrem = start_date_vrem
        for holiday_date in semester_holidays:
            if end_date_vrem == holiday_date:
                holiday_dates.append(holiday_date)
        start_date_vrem, end_date_vrem = adjust_dates_based_on_week_type(start_date_vrem, end_date_vrem,
                                                                         type_weekStart, week_type)
        type_weekStart = get_current_week_type(start_date_vrem)
    return holiday_dates, start_date_vrem, end_date_vrem, type_weekStart

def handle_empty_holidays(cal, entry, start_date, week_type, end_date):
    creator = EventCreator()
    creator.create_event(cal, entry, start_date, start_date, week_type, end_date, entry.get("Семестр"))
def handle_single_holiday(cal ,entry, start_date,end_date, week_type, type_weekStart,holiday_dates):
    holiday_date = holiday_dates[0]
    creator = EventCreator()
    creator.create_event(cal, entry, start_date, start_date, week_type,
                         holiday_date - timedelta(days=2), entry.get("Семестр"))
    start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                             type_weekStart, week_type)
    type_weekStart = get_current_week_type(start_date2)
    creator = EventCreator()
    creator.create_event(cal, entry, start_date2, end_date2, week_type,
                         end_date, entry.get("Семестр"))
    return holiday_date, start_date2, end_date2, type_weekStart

def handle_multiple_holidays(cal, entry, start_date2, end_date2, week_type, holiday_dates, type_weekStart, end_date):
    for i, holiday_date in enumerate(holiday_dates):
        if i == 0:
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                 holiday_date - timedelta(days=2), entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
        elif i == len(holiday_dates) - 1:
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                 holiday_dates[i] - timedelta(days=2), entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type, end_date,
                                 entry.get("Семестр"))
        else:
            holiday_date = holiday_dates[i]
            next_holiday_date = holiday_dates[i + 1]
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_dates[i], holiday_dates[i],
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
            while holiday_date == start_date2:
                start_date2, end_date2 = adjust_dates_based_on_week_type(start_date2, end_date2,
                                                                         type_weekStart, week_type)
                type_weekStart = get_current_week_type(start_date2)
            if holiday_date < start_date2:
                creator = EventCreator()
                creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                     next_holiday_date - timedelta(days=2), entry.get("Семестр"))
            else:
                creator = EventCreator()
                creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                     holiday_date - timedelta(days=2), entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_dates[i], holiday_dates[i],
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
    return start_date2, end_date2, week_type, holiday_dates, type_weekStart, end_date

def process_event_dates(cal, entry, start_date_str, end_date_str, week_type, semester_holidays):
    start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
    end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
    type_weekStart = get_current_week_type(start_date)
    holiday_dates, start_date_vrem, end_date_vrem, type_weekStart = collect_holiday_dates(start_date, end_date,
      type_weekStart, week_type,semester_holidays)
    print(holiday_dates)
    start_date2, end_date2 = start_date, start_date
    if not holiday_dates:
        handle_empty_holidays(cal, entry, start_date, week_type, end_date)
    elif len(holiday_dates) == 1:
        holiday_date, start_date2, end_date2, type_weekStart = handle_single_holiday(cal, entry, start_date, end_date,
          week_type, type_weekStart,holiday_dates)
    else:
        start_date2, end_date2, week_type, holiday_dates, type_weekStart, end_date = handle_multiple_holidays(cal,
          entry, start_date2,end_date2,week_type,holiday_dates,type_weekStart,end_date)

def collect_and_adjust_holiday_dates(current_date, end_semester, semester_holidays, week_type):
    type_weekStart = get_current_week_type(current_date)
    start_date = current_date
    holiday_dates = []

    while start_date <= end_semester:
        end_date = start_date
        for holiday_date in semester_holidays:
            if end_date == holiday_date:
                holiday_dates.append(holiday_date)
        start_date, end_date = adjust_dates_based_on_week_type(start_date, end_date,
                                                               type_weekStart, week_type)
        type_weekStart = get_current_week_type(start_date)

    print(holiday_dates)
    start_date2, end_date2 = current_date, current_date
    return type_weekStart, holiday_dates, start_date, start_date2, end_date2

def handle_no_holidays(cal, entry, current_date, week_type, end_semester):
    creator = EventCreator()
    creator.create_event(cal, entry, current_date, current_date, week_type, end_semester,
                         entry.get("Семестр"))
def handle_sing_holiday(cal, entry, current_date, week_type, type_weekStart, end_semester, holiday_dates):
    holiday_date = holiday_dates[0]
    creator = EventCreator()
    creator.create_event(cal, entry, current_date, current_date, week_type,
                         holiday_date - timedelta(days=2), entry.get("Семестр"))
    start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                             type_weekStart, week_type)
    type_weekStart = get_current_week_type(start_date2)
    creator = EventCreator()
    creator.create_event(cal, entry, start_date2, end_date2, week_type,
                         end_semester, entry.get("Семестр"))
    return holiday_date, start_date2, end_date2, type_weekStart

def handle_mult_holidays(cal, entry, start_date2, end_date2, week_type,holiday_dates, end_semester, used_break, type_weekStart):
    for i, holiday_date in enumerate(holiday_dates):
        if i == 0:
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type, holiday_date - timedelta(days=2),
                                 entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
        elif i == len(holiday_dates) - 1:
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                 holiday_dates[i] - timedelta(days=2), entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date,
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
            creator = EventCreator()
            creator.create_event(cal, entry, start_date2, end_date2, week_type, end_semester,
                                 entry.get("Семестр"))
            used_break = True
            break
        else:
            holiday_date = holiday_dates[i]
            next_holiday_date = holiday_dates[i + 1]
            while holiday_date == start_date2:
                start_date2, end_date2 = adjust_dates_based_on_week_type(start_date2, end_date2,
                                                                         type_weekStart,
                                                                         week_type)
                type_weekStart = get_current_week_type(start_date2)
            if holiday_date < start_date2:
                creator = EventCreator()
                creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                     next_holiday_date - timedelta(days=2),
                                     entry.get("Семестр"))
            else:
                creator = EventCreator()
                creator.create_event(cal, entry, start_date2, end_date2, week_type,
                                     holiday_date - timedelta(days=2),
                                     entry.get("Семестр"))
            start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_dates[i], holiday_dates[i],
                                                                     type_weekStart, week_type)
            type_weekStart = get_current_week_type(start_date2)
    return start_date2, end_date2, week_type,holiday_dates, end_semester, used_break

def process_weekly_schedule(cal, entry, semester_start,semester_holidays, week_type):
    current_date = semester_start
    end_semester = get_current_semester_end()
    while current_date <= end_semester:
        if current_date.strftime("%A").lower() == entry.get("День недели").lower():
            type_weekStart, holiday_dates, start_date, start_date2, end_date2 = collect_and_adjust_holiday_dates(
                current_date, end_semester, semester_holidays, week_type)
            if not holiday_dates:
                handle_no_holidays(cal, entry, current_date, week_type, end_semester)
                break
            elif len(holiday_dates) == 1:
                holiday_date, start_date2, end_date2, type_weekStart = handle_sing_holiday(cal, entry, current_date,
                  week_type, type_weekStart,end_semester, holiday_dates)
                break
            else:
                used_break = False
                start_date2, end_date2, week_type, holiday_dates, end_semester, used_break = handle_mult_holidays(cal,
                  entry,start_date2,end_date2, week_type,holiday_dates,end_semester,used_break, type_weekStart)
                if used_break:
                    break
        current_date += timedelta(days=1)

def create_single_day_event(cal, entry):
    start_date_str = entry.get("Дата")
    start_date = datetime.strptime(start_date_str, "%Y.%m.%d")
    creator = EventCreator()
    creator.create_event(cal, entry, start_date, start_date, None, None, entry.get("Семестр"))
    return start_date_str, start_date

