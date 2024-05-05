import os
import csv
import html
import json
from utils import replace_slash, decode_special_chars, NoVerifyHTTPAdapter, shorten_filename, to_unicode_escape
from config import DB_DIR, CREATE_JSON_DIR
from db.db_operations import load_data_from_json, normalize_parameter, normalize_table_name


def process_schedule_response(response_schedule, semester, institute=None, speciality=None, group=None, teacher=None):
    # semester_id_mapping = {1: 8, 2: 4, 3: 3, 4: 2, 5: 1}
    semester_id_mapping = {8: 1, 4: 2, 3: 3, 2: 4, 1: 5}
    response_json = {}

    if semester in semester_id_mapping and semester not in [1, 2, 8]:
        if response_schedule.status_code == 200:
            try:
                # Извлечь корректный JSON из строки
                start_index = response_schedule.text.find("[")
                end_index = response_schedule.text.rfind("]") + 1
                json_data = response_schedule.text[start_index:end_index]

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

                if teacher:
                    output_json_file = f"schedule_{semester}__{normalize_table_name(teacher)}.json"
                    param_search = f"schedule_{semester}||{teacher}"
                else:
                    output_json_file = f"schedule_{semester}__{normalize_table_name(institute)}__{normalize_table_name(speciality)}__{normalize_table_name(group)}.json"
                    param_search = f"schedule_{semester}||{institute}||{speciality}||{group}"
                output_json_file = os.path.join(CREATE_JSON_DIR, output_json_file)
                output_json_file = shorten_filename(output_json_file)

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
                        "Тип занятия": entry["lessontype"],
                        "Группа": entry["subgroup"],
                        "Начало": entry["starttime"],
                        "Конец": entry["endtime"],
                        "Семестр": semester_id_mapping.get(semester),
                        "Файл": replace_slash(param_search)
                    }
                    processed_data.append(processed_entry)
                    print(processed_entry)

                response_json = json.dumps(processed_data, indent=4, ensure_ascii=False)

                # Вывести данные в консоль
                for entry in processed_data:
                    print(json.dumps(entry, indent=4, ensure_ascii=False))

                # Сохранить данные в JSON файл
                with open(output_json_file, "w", encoding="utf-8") as json_file:
                    json.dump(processed_data, json_file, indent=4,
                              ensure_ascii=False)

                print(
                    f"Данные успешно обработаны и сохранены в {output_json_file}.")
                load_data_from_json(output_json_file)
            except Exception as e:
                print(f"Произошла ошибка при обработке расписания: {e}")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")
    else:
        # print("Неверный семестр для обработки.")
        if response_schedule.status_code == 200:
            try:
                content = response_schedule.text.replace("z[[", "").replace("]]", "")

                # Разделить данные на строки
                data_rows = content.split("],[")

                # Преобразование данных в формат JSON
                processed_data = []
                first_row_skipped = False  # Флаг для пропуска первой строки данных
                semester_param = normalize_table_name(normalize_parameter(str(semester)))
                institute_param = normalize_parameter(institute) if institute else None
                speciality_param = normalize_parameter(speciality) if speciality else None
                group_param = normalize_parameter(group) if group else None
                teacher_param = normalize_table_name(teacher if teacher else "")

                print(semester_param)
                print(institute)
                print(speciality)
                print(group)
                output_json_file = f"schedule_{semester_param}__"
                if teacher and institute is None:
                    output_json_file += f"{teacher_param}.json"
                    output_json_file = shorten_filename(output_json_file)
                    param_search = f"schedule_{semester}||{teacher}"
                else:
                    institute_name = normalize_table_name(institute) if institute else ""
                    speciality_name = normalize_table_name(speciality) if speciality else ""
                    group_name = normalize_table_name(group) if group else ""
                    output_json_file += f"{institute_name}__{speciality_name}__{group_name}.json"
                    output_json_file = shorten_filename(output_json_file)
                    param_search = f"schedule_{semester}||{institute}||{speciality}||{group}"
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
                        subject_2 = subject_parts[0].replace("<b>", "").replace("</b>", "").strip()
                        group_raw = subject_parts[-1].strip() if len(subject_parts) > 1 else ""
                        audi_2 = subject_parts[-2].strip() if len(subject_parts) > 2 else ""
                        lesson_type_raw = subject_parts[-3].strip() if len(subject_parts) > 3 else ""
                        teacher_param = normalize_table_name(teacher if teacher else "")

                        lesson_type = lesson_type_raw.replace("<sup><i>", "").replace("</i></sup>", "")

                        processed_row = {
                            "День недели": replace_slash(day_of_week).replace("/>", ""),
                            "Дата": replace_slash(date).replace("<br", ""),
                            "Время": replace_slash(time).replace("<br", "").replace("/>", "- "),
                            "Название предмета": replace_slash(subject_2),
                            "Группа": replace_slash(group_raw),
                            "Аудитория": replace_slash(audi_2),
                            "Тип занятия": replace_slash(lesson_type),
                            "Семестр": semester_id_mapping.get(semester),
                            "Файл": replace_slash(to_unicode_escape(param_search))
                        }
                        if processed_row is not None:
                            processed_data.append(processed_row)
                            #print(f"processed_data: {processed_row}")
                    else:
                        print("Неправильный формат данных:", row)

                processed_data = decode_special_chars(processed_data)
                response_json = json.dumps(processed_data, indent=4, ensure_ascii=False)
                try:
                    with open(output_json_file, "w", encoding="utf-8") as json_file:
                        json.dump(processed_data, json_file, indent=4,
                                  ensure_ascii=False)
                except Exception as e:
                    print(f"Произошла ошибка при записи данных в JSON файл: {e}")

                print(f"Данные успешно обработаны и сохранены в {output_json_file}.")
                load_data_from_json(output_json_file)
            except Exception as e:
                print(f"Произошла ошибка при обработке расписания: {e}")
        else:
            print(
                f"Ошибка запроса для расписания. Код статуса: {response_schedule.status_code}")
    return response_json

