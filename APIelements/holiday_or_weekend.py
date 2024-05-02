import requests
from icalendar import Calendar
import json
from datetime import datetime

def extract_holidays(url):
    current_year = datetime.now().year
    response = requests.get(url)
    if response.status_code == 200:
        cal = Calendar.from_ical(response.text)
        holidays = []
        for event in cal.walk('vevent'):
            date = event.get('dtstart').dt
            if date.year == current_year:
                summary = event.get('summary')
                date_str = date.strftime('%Y-%m-%d')
                holidays.append({'date': date_str, 'name': summary})
        return json.dumps(holidays, indent=4, ensure_ascii=False)
    else:
        print("Не удалось получить данные")
        return '[]'

url = "https://calendar.google.com/calendar/ical/ru.russian%23holiday%40group.v.calendar.google.com/public/basic.ics"

holidays_json = extract_holidays(url)

print("Праздники извлечены в формате JSON:")
print(holidays_json)
