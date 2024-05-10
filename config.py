import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
THIRD_ELEMENTS_DIR = os.path.join(BASE_DIR, "thirdElements")
CREATE_JSON_DIR = os.path.join(BASE_DIR, "createJSON")
CREATE_JSON_DIR_JSON = os.path.join(CREATE_JSON_DIR, "jsonAndIcal")
DB_DIR = os.path.join(BASE_DIR, "db")
PYTHON_EXE = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
CAL_UTILS_DIR = os.path.join(BASE_DIR, "calUtils")
START_CREATE_CAL_SCRIPT = os.path.join(CAL_UTILS_DIR, "startCreateCAL.py")
START_CREATE_JSON_SCRIPT = os.path.join(CREATE_JSON_DIR, "startJSON.py")
START_ALL_SCRIPT = os.path.join(BASE_DIR, "scriptStart.py")
GOOGLE_CAL = os.path.join(BASE_DIR, "add_events_from_ics_to_google_calendar.py")
TELEGRAM_API_TOKEN = "6918298485:AAG9b4gwPkIQvt1_9A3LOnFl2gMrDk3H5zw"
CERT_SEL = os.path.join(BASE_DIR, "server.pem")
KEY_SEL = os.path.join(BASE_DIR, "server.key")
LOC_SERVER = os.path.join(BASE_DIR, "fsfs.py")
NGROK = os.path.join(BASE_DIR, "drivers", "ngrok.exe")
NGROK_CONFIG_PATH = r'C:\Users\Home\AppData\Local\ngrok\ngrok.yml'
OUTPUT_SCHEDULE_FILE = os.path.join(THIRD_ELEMENTS_DIR, "output_schedule.php")
PROCESSED_SCHEDULE_DATA_FILE = os.path.join(CREATE_JSON_DIR, "processed_schedule_data.json")