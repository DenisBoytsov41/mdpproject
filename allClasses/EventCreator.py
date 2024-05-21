# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vRecur
from calUtils.semester_utils import *

class EventCreator:
    """Класс для работы с событиями календаря"""
    def __init__(self):
        pass

    # Основной метод для создания события.
    def create_event(self, cal, entry, start_date, end_date, week_type, end_semester, semester):
        event = Event()
        description = self.event_description(entry, semester)
        event.add('description', description)
        start_time_str, end_time_str, start_time, end_time = self.work_with_time(entry)

        if week_type is not None:
            rule = vRecur(freq='weekly')
            rule, start_date, end_date, sem_start = self.work_with_rule(rule, week_type, start_date, end_date, end_semester)
            event.add('rrule', rule)

        # Проверяем, что end_semester больше start_date
        if (end_semester is not None and end_semester > start_date) or end_semester is None:
            cal, event = self.work_with_event(event, cal, start_date, end_date, start_time, end_time, entry, week_type)
        else:
            print("Ошибка: Дата окончания семестра должна быть позже даты начала.")

    # Добавляем описание события.
    def event_description(self, entry, semester):
        """Метод для генерации описания события."""
        if semester != 2 and semester != 3:
            description = f'{entry["Тип занятия"]} \nПреподаватель/Группа: {entry["Группа"]}\nАудитория: {entry["Аудитория"]}'
        else:
            description = f'{entry["Тип занятия"]} \nПреподаватель/Группа: {entry["ФИО преподавателя"]}\nАудитория: {entry["Аудитория"]}'

        if entry.get("Группа"):
            description += f'\nГруппа: {entry["Группа"]}'
        return description

    # Получаем время начала и окончания события.
    def work_with_time(self, entry):
        """Метод для обработки времени события."""
        start_time_str, end_time_str = entry["Время"].split(" - ")
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")
        return start_time_str, end_time_str, start_time, end_time

    # Получаем обновленные данные правила.
    def work_with_rule(self, rule, week_type, start_date, end_date, end_semester):
        """Метод для настройки правила повторения события."""
        if week_type == "Под чертой" or week_type == "Над чертой":
            rule['interval'] = 2
        else:
            rule['interval'] = 1

        sem_start = get_current_semester_start()

        if week_type == "Над чертой" and start_date - sem_start <= timedelta(days=7):
            start_date += timedelta(days=7)
            end_date += timedelta(days=7)

        rule['until'] = end_semester + timedelta(days=1)  # Устанавливаем дату окончания
        return rule, start_date, end_date, sem_start

    # Добавляем событие в календарь.
    def work_with_event(self, event, cal, start_date, end_date, start_time, end_time, entry, week_type):
        """Метод для добавления события в календарь."""
        event.add('dtstart', start_date + timedelta(hours=start_time.hour, minutes=start_time.minute))
        event.add('dtend', end_date + timedelta(hours=end_time.hour, minutes=end_time.minute))
        event.add('summary', f'{entry["Название предмета"]} ({week_type})' if week_type else entry["Название предмета"])
        event.add('location', entry["Аудитория"])

        cal.add_component(event)
        return cal, event
