# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from tkinter import filedialog
from icalendar import Calendar, Event
from icalendar import vRecur
from calUtils.semester_utils import (get_current_week_type, get_current_semester_start,
                            get_current_semester_end, adjust_dates_based_on_week_type, save_calendar, add_semester_holidays)
from APIelements.holiday_or_weekend import extract_holidays
from allClasses.EventCreator import EventCreator

class CalendarCreator:
    def __init__(self):
        self.cal = Calendar()
        self.cal.add('prodid', '-//KSU//RU')
        self.cal.add('version', '2.0')

    def fetch_holidays(self, url):
        holidays_response = extract_holidays(url)
        holidays_json = json.loads(holidays_response)
        return holidays_json

    def create_icalendar(self, data, output_json_file=None):
        url = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"
        holidays_json = self.fetch_holidays(url)

        semester_start = get_current_semester_start()
        semester_end = get_current_semester_end()

        semester_holidays = add_semester_holidays(holidays_json, semester_start, semester_end)

        for entry in data:
            if entry.get("Семестр") in [2, 3]:
                self.handle_semester_event(entry, semester_holidays)
            else:
                self.handle_regular_event(entry)

        save_calendar(self.cal, output_json_file)

    def handle_semester_event(self, entry, semester_holidays):
        start_date_str = entry.get("Начало")
        end_date_str = entry.get("Конец")
        week_type = entry.get("Тип недели")

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
            self.process_dates(entry, start_date, end_date, week_type, semester_holidays)
        else:
            self.process_weekly_event(entry, semester_holidays)

    def handle_regular_event(self, entry):
        start_date_str = entry.get("Дата")
        start_date = datetime.strptime(start_date_str, "%Y.%m.%d")
        creator = EventCreator()
        creator.create_event(self.cal, entry, start_date, start_date, None, None, entry.get("Семестр"))

    def process_dates(self, entry, start_date, end_date, week_type, semester_holidays):
        type_week_start = get_current_week_type(start_date)
        holiday_dates = []
        start_date_temp = start_date

        while start_date_temp <= end_date:
            end_date_temp = start_date_temp
            for holiday_date in semester_holidays:
                if end_date_temp == holiday_date:
                    holiday_dates.append(holiday_date)
            start_date_temp, end_date_temp = adjust_dates_based_on_week_type(start_date_temp, end_date_temp, type_week_start, week_type)
            type_week_start = get_current_week_type(start_date_temp)

        if not holiday_dates:
            creator = EventCreator()
            creator.create_event(self.cal, entry, start_date, start_date, week_type, end_date, entry.get("Семестр"))
        else:
            self.process_holidays(entry, start_date, end_date, week_type, holiday_dates)

    def process_weekly_event(self, entry, semester_holidays):
        current_date = get_current_semester_start()
        end_semester = get_current_semester_end()

        while current_date <= end_semester:
            if current_date.strftime("%A").lower() == entry.get("День недели").lower():
                type_week_start = get_current_week_type(current_date)
                start_date = current_date
                holiday_dates = []

                while start_date <= end_semester:
                    end_date = start_date
                    for holiday_date in semester_holidays:
                        if end_date == holiday_date:
                            holiday_dates.append(holiday_date)
                    start_date, end_date = adjust_dates_based_on_week_type(start_date, end_date, type_week_start, entry.get("Тип недели"))
                    type_week_start = get_current_week_type(start_date)

                self.process_holidays(entry, current_date, end_semester, entry.get("Тип недели"), holiday_dates)
                break

            current_date += timedelta(days=1)

    def process_holidays(self, entry, start_date, end_date, week_type, holiday_dates):
        if len(holiday_dates) == 1:
            self.create_event_with_one_holiday(entry, start_date, end_date, week_type, holiday_dates)
        else:
            self.create_event_with_multiple_holidays(entry, start_date, end_date, week_type, holiday_dates)

    def create_event_with_one_holiday(self, entry, start_date, end_date, week_type, holiday_dates):
        holiday_date = holiday_dates[0]
        creator = EventCreator()
        creator.create_event(self.cal, entry, start_date, start_date, week_type, holiday_date - timedelta(days=2), entry.get("Семестр"))

        start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date, get_current_week_type(holiday_date), week_type)
        creator.create_event(self.cal, entry, start_date2, end_date2, week_type, end_date, entry.get("Семестр"))

    def create_event_with_multiple_holidays(self, entry, start_date, end_date, week_type, holiday_dates):
        used_break = False
        for i, holiday_date in enumerate(holiday_dates):
            if i == 0:
                self.create_initial_event(entry, start_date, end_date, week_type, holiday_date)
            elif i == len(holiday_dates) - 1:
                self.create_final_event(entry, holiday_dates, i, end_date, week_type)
                used_break = True
                break
            else:
                self.create_intermediate_event(entry, holiday_dates, i, week_type)

            if used_break:
                break

    def create_initial_event(self, entry, start_date, end_date, week_type, holiday_date):
        creator = EventCreator()
        creator.create_event(self.cal, entry, start_date, end_date, week_type, holiday_date - timedelta(days=2), entry.get("Семестр"))

    def create_final_event(self, entry, holiday_dates, i, end_date, week_type):
        holiday_date = holiday_dates[i]
        start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date, get_current_week_type(holiday_date), week_type)
        creator = EventCreator()
        creator.create_event(self.cal, entry, start_date2, end_date2, week_type, holiday_dates[i] - timedelta(days=2), entry.get("Семестр"))

        start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date, get_current_week_type(holiday_date), week_type)
        creator.create_event(self.cal, entry, start_date2, end_date2, week_type, end_date, entry.get("Семестр"))

    def create_intermediate_event(self, entry, holiday_dates, i, week_type):
        holiday_date = holiday_dates[i]
        next_holiday_date = holiday_dates[i + 1]
        start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date, get_current_week_type(holiday_date), week_type)

        while holiday_date == start_date2:
            start_date2, end_date2 = adjust_dates_based_on_week_type(start_date2, end_date2, get_current_week_type(start_date2), week_type)

        if holiday_date < start_date2:
            creator = EventCreator()
            creator.create_event(self.cal, entry, start_date2, end_date2, week_type, next_holiday_date - timedelta(days=2), entry.get("Семестр"))
        else:
            creator = EventCreator()
            creator.create_event(self.cal, entry, start_date2, end_date2, week_type, holiday_date - timedelta(days=2), entry.get("Семестр"))

        start_date2, end_date2 = adjust_dates_based_on_week_type(holiday_date, holiday_date, get_current_week_type(holiday_date), week_type)

