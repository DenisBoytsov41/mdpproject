import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
THIRD_ELEMENTS_DIR = os.path.join(BASE_DIR, "thirdElements")
CREATE_JSON_DIR = os.path.join(BASE_DIR, "createJSON")

OUTPUT_SCHEDULE_FILE = os.path.join(THIRD_ELEMENTS_DIR, "output_schedule.php")
PROCESSED_SCHEDULE_DATA_FILE = os.path.join(CREATE_JSON_DIR, "processed_schedule_data.json")