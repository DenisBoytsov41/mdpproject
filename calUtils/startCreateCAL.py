import json
import locale
import sys
from calendar_utils import create_icalendar, create_event
from json_utils import read_json_file
from gui_utils import get_file_path


locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

if __name__ == "__main__":
    file_path = get_file_path()
    #schedule_json = json.loads(sys.argv[1])

    if file_path:
        data = read_json_file(file_path)
        if data:
            create_icalendar(data)
