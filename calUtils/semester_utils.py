import os  # Импорт модуля os для работы с файловой системой.
from datetime import datetime, timedelta  # Импорт необходимых классов из модуля datetime.
from tkinter import filedialog  # Импорт функции filedialog для работы с диалоговыми окнами.

def get_current_week_type(start_date, current_date=None):
    """Функция определяет тип текущей недели (над или под чертой) относительно указанной даты начала семестра."""
    if current_date is None:
        current_date = get_current_semester_start()  # Получаем текущую дату начала семестра, если она не была указана.

    while start_date.weekday() != 0:  # Пока день недели начальной даты не равен понедельнику.
        start_date -= timedelta(days=1)  # Уменьшаем начальную дату на один день.

    weeks_passed = abs((current_date - start_date).days) // 7  # Вычисляем количество прошедших недель с начала семестра.

    return "Под чертой" if weeks_passed % 2 == 0 or weeks_passed == 0 else "Над чертой"  # Определяем тип недели.

def get_current_semester_start():
    """Функция определяет дату начала текущего семестра."""
    today = datetime.today()  # Получаем текущую дату.
    if today.month <= 8:  # Если текущий месяц меньше или равен 8 (сентябрь), то начало семестра весной.
        start_date = datetime(today.year, 2, 5)  # Устанавливаем начало семестра на 5 февраля текущего года.
    else:  # Иначе начало семестра осенью.
        start_date = datetime(today.year, 9, 1)  # Устанавливаем начало семестра на 1 сентября текущего года.

    while start_date.weekday() == 6:  # Пока начальная дата выпадает на воскресенье.
        start_date += timedelta(days=1)  # Увеличиваем начальную дату на один день.

    return start_date  # Возвращаем дату начала семестра.

def get_current_semester_end():
    """Функция определяет дату окончания текущего семестра."""
    start_date = get_current_semester_start()  # Получаем дату начала текущего семестра.
    if start_date.month < 2 or (start_date.month == 2 and start_date.day < 5):  # Если начало семестра до февраля или в феврале до 5 числа.
        end_date = datetime(start_date.year, 12, 30)  # Устанавливаем окончание семестра на 30 декабря текущего года.
    else:  # Иначе начало семестра после февраля и позже 5 числа.
        end_date = datetime(start_date.year, 6, 30)  # Устанавливаем окончание семестра на 30 июня следующего года.

    return end_date  # Возвращаем дату окончания семестра.

def adjust_dates_based_on_week_type(start_date, end_date, type_weekStart, week_type):
    """Функция корректирует даты начала и окончания события в зависимости от типа недели."""
    if (week_type == "Над чертой" or week_type == "Под чертой") and week_type == type_weekStart:
        start_date += timedelta(days=14)  # Увеличиваем начальную дату на 14 дней.
        end_date += timedelta(days=14)  # Увеличиваем конечную дату на 14 дней.
    elif (week_type == "Над чертой" or week_type == "Под чертой") and week_type != type_weekStart:
        start_date += timedelta(days=7)  # Увеличиваем начальную дату на 7 дней.
        end_date += timedelta(days=7)  # Увеличиваем конечную дату на 7 дней.
    elif week_type == "Общая":
        start_date += timedelta(days=7)  # Увеличиваем начальную дату на 7 дней.
        end_date += timedelta(days=7)  # Увеличиваем конечную дату на 7 дней.
    return start_date, end_date  # Возвращаем скорректированные даты начала и окончания.

def save_calendar(cal, output_json_file = None):
    """Функция сохраняет календарь в файл формата iCalendar (.ics)."""
    if output_json_file is not None:
        directory = os.path.join(os.path.dirname(output_json_file), "ICAL")  # Получаем путь к папке ICAL в той же директории, где находится файл JSON.
        if not os.path.exists(directory):  # Если такая папка не существует.
            os.makedirs(directory)  # Создаем ее.
        filename = os.path.splitext(os.path.basename(output_json_file))[0] + ".ics"  # Получаем имя файла без расширения JSON и добавляем расширение .ics.
        file_path = os.path.join(directory, filename)  # Получаем полный путь к файлу.
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())  # Записываем календарь в файл в формате iCalendar.
    else:
        file_path = filedialog.asksaveasfilename(defaultextension=".ics", filetypes=[("iCalendar files", "*.ics")])  # Открываем диалоговое окно для сохранения файла.
        if file_path:  # Если выбрано место сохранения файла.
            with open(file_path, 'wb') as f:
                f.write(cal.to_ical())  # Записываем календарь в выбранный файл.

def add_semester_holidays(holidays_json, semester_start, semester_end):
    """Функция добавляет праздничные даты семестра из JSON в словарь."""
    semester_holidays = {}  # Создаем пустой словарь для хранения праздничных дат семестра.
    for holiday in holidays_json:  # Проходимся по каждому празднику в JSON.
        holiday_date = datetime.strptime(holiday['date'],
                                         "%Y-%m-%d")  # Преобразуем строковое представление даты праздника в объект datetime.
        if semester_start <= holiday_date <= semester_end:  # Если праздник попадает в интервал семестра.
            semester_holidays[holiday_date] = holiday_date  # Добавляем праздничную дату в словарь.
    return semester_holidays  # Возвращаем словарь праздничных дат семестра.
