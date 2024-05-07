import os
from datetime import datetime, timedelta
from tkinter import filedialog


def get_current_week_type(start_date, current_date=None):
    if current_date is None:
        current_date = get_current_semester_start()

    while start_date.weekday() != 0:
        start_date -= timedelta(days=1)

    weeks_passed = abs((current_date - start_date).days) // 7

    return "Под чертой" if weeks_passed % 2 == 0 or weeks_passed == 0 else "Над чертой"

def get_current_semester_start():
    today = datetime.today()
    if today.month <= 8:
        start_date = datetime(today.year, 2, 5)
    else:
        start_date = datetime(today.year, 9, 1)

    while start_date.weekday() == 6:
        start_date += timedelta(days=1)

    return start_date

def get_current_semester_end():
    start_date = get_current_semester_start()
    if start_date.month < 2 or (start_date.month == 2 and start_date.day < 5):
        end_date = datetime(start_date.year, 12, 30)
    else:
        end_date = datetime(start_date.year, 6, 30)

    return end_date

def adjust_dates_based_on_week_type(start_date, end_date, type_weekStart, week_type):
    if (week_type == "Над чертой" or week_type == "Под чертой") and week_type == type_weekStart:
        start_date += timedelta(days=14)
        end_date += timedelta(days=14)
    elif (week_type == "Над чертой" or week_type == "Под чертой") and week_type != type_weekStart:
        start_date += timedelta(days=7)
        end_date += timedelta(days=7)
    elif week_type == "Общая":
        start_date += timedelta(days=7)
        end_date += timedelta(days=7)
    return start_date, end_date

def save_calendar(cal, output_json_file):
    directory = os.path.join(os.path.dirname(output_json_file), "ICAL")
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.splitext(os.path.basename(output_json_file))[0] + ".ics"
    file_path = os.path.join(directory, filename)
    with open(file_path, 'wb') as f:
        f.write(cal.to_ical())

def add_semester_holidays(holidays_json, semester_start, semester_end):
    semester_holidays = {}
    for holiday in holidays_json:
        holiday_date = datetime.strptime(holiday['date'], "%Y-%m-%d")
        if semester_start <= holiday_date <= semester_end:
            semester_holidays[holiday_date] = holiday_date
    return semester_holidays