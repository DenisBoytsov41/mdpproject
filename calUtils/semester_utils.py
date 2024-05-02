from datetime import datetime, timedelta

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
