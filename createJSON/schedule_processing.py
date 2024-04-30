import os
import csv
import html
import json
from utils import replace_slash, decode_special_chars, NoVerifyHTTPAdapter


def process_schedule_response(response_schedule, semester):
    # semester_id_mapping = {1: 8, 2: 4, 3: 3, 4: 2, 5: 1}
    semester_id_mapping = {8: 1, 4: 2, 3: 3, 2: 4, 1: 5}

    if semester in semester_id_mapping and semester not in [1, 2, 8]:
        if response_schedule.status_code == 200:
            try:
                output_file_path = os.path.join("..", "thirdElements", "output_schedule.php")
                # Записываем результат запроса в файл
                with open(output_file_path, "w", encoding="utf-8") as file:
                    file.write(response_schedule.text)

                print("Файл успешно получен и сохранен как output_schedule.php.")

                # Загрузить данные из файла
                with open(output_file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                # Извлечь корректный JSON из строки
                start_index = content.find("[")
                end_index = content.rfind("]") + 1
                json_data = content[start_index:end_index]

                # Преобразовать данные
                data = json.loads(json_data)

                # Маппинг для типов недели
                week_mapping = {"2": "Под чертой", "1": "Над чертой", "0": "Общая"}

                # Маппинг для дней недели
                day_mapping = {"1": "Понедельник", "2": "Вторник", "3": "Среда",
                               "4": "Четверг", "5": "Пятница", "6": "Суббота"}

                # Маппинг для времени пар
                time_mapping = {"1": "8:30 - 10:00", "2": "10:10 - 11:40",
                                "3": "11:50 - 13:20", "4": "14:00 - 15:30",
                                "5": "15:40 - 17:10", "6": "17:20 - 18:50",
                                "7": "19:00 - 20:30"}

                # Преобразовать данные
                processed_data = []
                for entry in data:
                    processed_entry = {
                        "День недели": day_mapping.get(entry["x"], entry["x"]),
                        "Время": time_mapping.get(entry["y"], entry["y"]),
                        "Тип недели": week_mapping.get(entry["n"], entry["n"]),
                        "Название предмета": entry["subject1"],
                        "Аудитория": entry["subject2"],
                        "ФИО преподавателя": entry["subject3"],
                        "Тип занятия:": entry["lessontype"],
                        "Группа": entry["subgroup"],
                        "Начало": entry["starttime"],
                        "Конец": entry["endtime"],
                        "Семестр": semester_id_mapping.get(semester)
                    }
                    processed_data.append(processed_entry)

                # Вывести данные в консоль
                for entry in processed_data:
                    print(json.dumps(entry, indent=4, ensure_ascii=False))
                    print()

                # Сохранить данные в JSON файл
                output_json_file = "processed_schedule_data.json"
                with open(output_json_file, "w", encoding="utf-8") as json_file:
                    json.dump(processed_data, json_file, indent=4,
                              ensure_ascii=False)

                print(
                    f"Данные успешно обработаны и сохранены в {output_json_file}.")
            except Exception as e:
                print(f"Произошла ошибка при обработке расписания: {e}")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")
    else:
        # print("Неверный семестр для обработки.")
        if response_schedule.status_code == 200:
            try:
                output_file_path = os.path.join("..", "thirdElements", "output_schedule.php")
                with open(output_file_path, "w", encoding="utf-8") as file:
                    file.write(response_schedule.text)

                print("Файл успешно получен и сохранен как output_schedule.php.")
                # Загрузить данные из файла
                with open(output_file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                content = content.replace("z[[", "").replace("]]", "")

                # Разделить данные на строки
                data_rows = content.split("],[")

                # Преобразование данных в формат JSON
                processed_data = []
                first_row_skipped = False  # Флаг для пропуска первой строки данных
                for row in data_rows:
                    if not first_row_skipped:
                        first_row_skipped = True
                        continue  # Пропустить первую строку данных
                    values = list(csv.reader([row], delimiter=','))[0]
                    if len(values) == 4:
                        day_of_week = html.unescape(values[0].strip('"').split()[1])  # Извлечение только дня недели
                        date_parts = html.unescape(values[0].strip('"').split()[0]).split('.')
                        date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"  # Преобразование формата даты
                        time = html.unescape(values[1].strip('"')).replace("<br />", " ")
                        # Декодирование HTML-спецсимволов

                        values_two = ["".join(values[2])]

                        values_two = [replace_slash(value) for value in values_two]

                        for i in range(len(values)):
                            values[i] = [replace_slash(values[i])]

                        subject_and_teacher = html.unescape(values_two[0].strip('"'))

                        subject_parts = subject_and_teacher.split("<br />")

                        # Извлечение данных
                        subject = subject_parts[0].replace("<b>", "").replace("</b>", "").strip()
                        audience_raw = subject_parts[-1].strip() if len(subject_parts) > 1 else ""
                        teacher = subject_parts[-2].strip() if len(subject_parts) > 2 else ""
                        lesson_type_raw = subject_parts[-3].strip() if len(subject_parts) > 3 else ""

                        lesson_type = lesson_type_raw.replace("<sup><i>", "").replace("</i></sup>", "")

                        processed_row = {
                            "День недели": replace_slash(day_of_week).replace("/>", ""),
                            "Дата": replace_slash(date).replace("<br", ""),
                            "Время": replace_slash(time).replace("<br", "").replace("/>", "- "),
                            "Название предмета": replace_slash(subject),
                            "Аудитория": replace_slash(audience_raw),
                            "ФИО преподавателя": replace_slash(teacher),
                            "Тип занятия": replace_slash(lesson_type),
                            "Семестр": semester_id_mapping.get(semester)
                        }

                        processed_data.append(processed_row)
                    else:
                        print("Неправильный формат данных:", row)

                processed_data = decode_special_chars(processed_data)
                # Сохранение обработанных данных в JSON файл
                output_json_file = "processed_schedule_data.json"
                with open(output_json_file, "w", encoding="utf-8") as json_file:
                    json.dump(processed_data, json_file, indent=4, ensure_ascii=False)

                print(f"Данные успешно обработаны и сохранены в {output_json_file}.")
            except Exception as e:
                print(f"Произошла ошибка при обработке расписания: {e}")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")
