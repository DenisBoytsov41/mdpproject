# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from icalendar import vRecur
from calUtils.semester_utils import (get_current_week_type, get_current_semester_start,
                            get_current_semester_end, adjust_dates_based_on_week_type, save_calendar, add_semester_holidays)
from APIelements.holiday_or_weekend import extract_holidays
from allClasses.EventCreator import EventCreator

class CalendarCreator:
    """Класс для создания iCalendar событий из данных и сохранения их в файл."""
    def __init__(self, use_holidays=True):
        self.use_holidays = use_holidays

    # Создает iCalendar файл из данных.
    def create_icalendar(self, data, output_json_file=None):
        """
        Создает iCalendar файл из данных.

        Аргументы:
            data (list): Список словарей с данными о событиях.
            output_json_file (str): Путь к файлу для сохранения iCalendar данных.
        """
        cal = Calendar()
        cal.add('prodid', '-//KSU//RU')
        cal.add('version', '2.0')

        semester_start = get_current_semester_start()
        semester_end = get_current_semester_end()
        semester_holidays = []

        if self.use_holidays:
            holidays_json = self.fetch_holidays()
            semester_holidays = add_semester_holidays(holidays_json, semester_start, semester_end)

        for entry in data:
            if entry.get("Семестр") in [2, 3]:
                start_date_str = entry.get("Начало")
                end_date_str = entry.get("Конец")
                week_type = entry.get("Тип недели")

                if start_date_str and end_date_str:
                    self.process_event_dates(cal, entry, start_date_str, end_date_str, week_type, semester_holidays)
                else:
                    self.process_weekly_schedule(cal, entry, semester_start, semester_holidays, week_type)
            else:
                start_date_str, start_date = self.create_single_day_event(cal, entry)
        save_calendar(cal, output_json_file)

    # Получает данные о праздниках
    def fetch_holidays(self):
        """
        Получает данные о праздниках.

        Возвращает:
            dict: Словарь с данными о праздниках.
        """
        url = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"
        holidays_response = extract_holidays(url)
        return json.loads(holidays_response)

    # Собирает даты праздников в течение заданного периода времени.
    def collect_holiday_dates(self, start_date, end_date, type_weekStart, week_type, semester_holidays):
        """
        Собирает даты праздников в течение заданного периода времени.

        Аргументы:
            start_date (datetime): Начальная дата периода.
            end_date (datetime): Конечная дата периода.
            type_weekStart (str): Тип начала недели.
            week_type (str): Тип недели.
            semester_holidays (list): Список праздников в семестре.

        Возвращает:
            list: Список дат праздников в течение заданного периода времени.
        """
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

    # Обрабатывает случай, когда нет праздников.
    def handle_empty_holidays(self, cal, entry, start_date, week_type, end_date):
        """
        Обрабатывает случай, когда нет праздников.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            start_date (datetime): Начальная дата события.
            week_type (str): Тип недели.
            end_date (datetime): Конечная дата события.
        """
        creator = EventCreator()
        creator.create_event(cal, entry, start_date, start_date, week_type, end_date, entry.get("Семестр"))

    # Обрабатывает случай, когда есть только один праздник.
    def handle_single_holiday(self, cal, entry, start_date, end_date, week_type, type_weekStart, holiday_dates):
        """
          Обрабатывает случай, когда есть только один праздник.

          Аргументы:
              cal (Calendar): Календарь, куда добавляются события.
              entry (dict): Словарь с данными о событии.
              start_date (datetime): Начальная дата события.
              end_date (datetime): Конечная дата события.
              week_type (str): Тип недели.
              type_weekStart (str): Тип начала недели.
              holiday_dates (list): Список праздников.

          Возвращает:
              tuple: Кортеж с данными о дате праздника, корректированных датах и типе начала недели.
          """
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

    # Обрабатывает случай, когда есть несколько праздников.
    def handle_multiple_holidays(self, cal, entry, start_date2, end_date2, week_type, holiday_dates, type_weekStart,
                                 end_date):
        """
        Обрабатывает случай, когда есть несколько праздников.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            start_date2 (datetime): Начальная дата события.
            end_date2 (datetime): Конечная дата события.
            week_type (str): Тип недели.
            holiday_dates (list): Список праздников.
            type_weekStart (str): Тип начала недели.
            end_date (datetime): Конечная дата события.

        Возвращает:
            tuple: Кортеж с данными о корректированных датах, типе недели, праздниках и флаге использования break.
        """
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

    # Обрабатывает даты событий
    def process_event_dates(self, cal, entry, start_date_str, end_date_str, week_type, semester_holidays):
        """
        Обрабатывает даты событий.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            start_date_str (str): Строка с начальной датой события.
            end_date_str (str): Строка с конечной датой события.
            week_type (str): Тип недели.
            semester_holidays (list): Список праздников в семестре.
        """
        start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
        end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
        type_weekStart = get_current_week_type(start_date)

        if self.use_holidays:
            holiday_dates, start_date_vrem, end_date_vrem, type_weekStart = self.collect_holiday_dates(start_date, end_date,
                                                                                                  type_weekStart, week_type,
                                                                                                  semester_holidays)
            print(holiday_dates)
        else:
            holiday_dates = []

        start_date2, end_date2 = start_date, start_date
        if not holiday_dates:
            self.handle_empty_holidays(cal, entry, start_date, week_type, end_date)
        elif len(holiday_dates) == 1:
            holiday_date, start_date2, end_date2, type_weekStart = self.handle_single_holiday(cal, entry, start_date,
                                                                                         end_date,
                                                                                         week_type, type_weekStart,
                                                                                         holiday_dates)
        else:
            start_date2, end_date2, week_type, holiday_dates, type_weekStart, end_date = self.handle_multiple_holidays(cal,
                                                                                                                  entry,
                                                                                                                  start_date2,
                                                                                                                  end_date2,
                                                                                                                  week_type,
                                                                                                                  holiday_dates,
                                                                                                                  type_weekStart,
                                                                                                                  end_date)

    # Собирает и корректирует даты праздников.
    def collect_and_adjust_holiday_dates(self, current_date, end_semester, semester_holidays, week_type):
        """
           Собирает и корректирует даты праздников.

           Аргументы:
               current_date (datetime): Текущая дата.
               end_semester (datetime): Конец семестра.
               semester_holidays (list): Список праздников в семестре.
               week_type (str): Тип недели.

           Возвращает:
               tuple: Кортеж с данными о датах праздников и корректированных датах.
           """

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

    # Обрабатывает случай, когда нет праздников.
    def handle_no_holidays(self, cal, entry, current_date, week_type, end_semester):
        """
           Обрабатывает случай, когда нет праздников.

           Аргументы:
               cal (Calendar): Календарь, куда добавляются события.
               entry (dict): Словарь с данными о событии.
               start_date (datetime): Начальная дата события.
               week_type (str): Тип недели.
               end_date (datetime): Конечная дата события.
           """
        creator = EventCreator()
        creator.create_event(cal, entry, current_date, current_date, week_type, end_semester,
                             entry.get("Семестр"))

    # Обрабатывает случай, когда есть только один праздник.
    def handle_sing_holiday(self, cal, entry, current_date, week_type, type_weekStart, end_semester, holiday_dates):
        """
        Обрабатывает случай, когда есть только один праздник.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            start_date (datetime): Начальная дата события.
            end_date (datetime): Конечная дата события.
            week_type (str): Тип недели.
            type_weekStart (str): Тип начала недели.
            holiday_dates (list): Список праздников.

        Возвращает:
            tuple: Кортеж с данными о дате праздника, корректированных датах и типе начала недели.
        """
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

    #  Обрабатывает случай, когда есть несколько праздников.
    def handle_mult_holidays(self, cal, entry, start_date2, end_date2, week_type, holiday_dates, end_semester, used_break,
                             type_weekStart):
        """
        Обрабатывает случай, когда есть несколько праздников.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            start_date2 (datetime): Начальная дата события.
            end_date2 (datetime): Конечная дата события.
            week_type (str): Тип недели.
            holiday_dates (list): Список праздников.
            type_weekStart (str): Тип начала недели.
            end_date (datetime): Конечная дата семестра.

        Возвращает:
            tuple: Кортеж с обновленными данными о датах и типе недели, списком праздников,
                конечной датой семестра и флагом использования прерывания.
        """
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
        return start_date2, end_date2, week_type, holiday_dates, end_semester, used_break

    # Обрабатывает еженедельное расписание.
    def process_weekly_schedule(self, cal, entry, semester_start, semester_holidays, week_type):
        """
        Обрабатывает еженедельное расписание.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.
            semester_start (datetime): Начало семестра.
            semester_holidays (list): Список праздников в семестре.
            week_type (str): Тип недели.
        """
        current_date = semester_start
        end_semester = get_current_semester_end()
        while current_date <= end_semester:
            if current_date.strftime("%A").lower() == entry.get("День недели").lower():
                type_weekStart, holiday_dates, start_date, start_date2, end_date2 = self.collect_and_adjust_holiday_dates(
                    current_date, end_semester, semester_holidays, week_type)

                if not self.use_holidays or not holiday_dates:
                    self.handle_no_holidays(cal, entry, current_date, week_type, end_semester)
                    break
                elif len(holiday_dates) == 1:
                    holiday_date, start_date2, end_date2, type_weekStart = self.handle_sing_holiday(cal, entry, current_date,
                                                                                               week_type,
                                                                                               type_weekStart,
                                                                                               end_semester,
                                                                                               holiday_dates)
                    break
                else:
                    used_break = False
                    start_date2, end_date2, week_type, holiday_dates, end_semester, used_break = self.handle_mult_holidays(
                        cal,
                        entry, start_date2, end_date2, week_type, holiday_dates, end_semester, used_break,
                        type_weekStart)
                    if used_break:
                        break
            current_date += timedelta(days=1)

    # Создает событие на один день.
    def create_single_day_event(self, cal, entry):
        """
        Создает событие на один день.

        Аргументы:
            cal (Calendar): Календарь, куда добавляются события.
            entry (dict): Словарь с данными о событии.

        Возвращает:
            tuple: Кортеж с данными о строке начальной даты и объекте начальной даты.
        """
        start_date_str = entry.get("Дата")
        start_date = datetime.strptime(start_date_str, "%Y.%m.%d")
        creator = EventCreator()
        creator.create_event(cal, entry, start_date, start_date, None, None, entry.get("Семестр"))
        return start_date_str, start_date