import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from icalendar import Calendar

CLIENT_SECRETS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost:8080/'

def add_events_to_google_calendar(service, ics_file_path):
    with open(ics_file_path, 'rb') as f:
        calendar = Calendar.from_ical(f.read())

    new_calendar = {
        'summary': 'NewCalendar',
        'timeZone': 'Europe/Moscow'
    }
    created_calendar = service.calendars().insert(body=new_calendar).execute()
    calendar_id = created_calendar['id']

    for event in calendar.walk('VEVENT'):
        event_summary = str(event.get('summary'))
        event_description = str(event.get('description'))
        event_location = str(event.get('location'))  # Извлечение атрибута LOCATION
        event_start = event.get('dtstart').dt
        event_end = event.get('dtend').dt
        event_rrule = str(event.get('rrule'))  # Извлечение атрибута RRULE

        event_start = event_start.strftime('%Y-%m-%dT%H:%M:%S') + '+03:00'
        event_end = event_end.strftime('%Y-%m-%dT%H:%M:%S') + '+03:00'

        event_body = {
            'summary': event_summary,
            'description': event_description,
            'location': event_location,
            'start': {'dateTime': event_start},
            'end': {'dateTime': event_end}
        }

        # Если атрибут RRULE присутствует, добавляем его в тело запроса
        if event_rrule:
            event_body['recurrence'] = [event_rrule]

        service.events().insert(calendarId=calendar_id, body=event_body).execute()

    print("События успешно добавлены в новый календарь Google.")

def authenticate_google_calendar():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

    print("Пожалуйста, авторизуйтесь по следующей ссылке:")
    print(authorization_url)

    if input("Введите полученный код авторизации: "):
        credentials = flow.run_local_server()
        service = build('calendar', 'v3', credentials=credentials)
        return service
    else:
        print("Не удалось выполнить аутентификацию.")
        return None

def main():
    subprocess_ics_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    if subprocess_ics_file_path:
        ics_file_path = subprocess_ics_file_path
    else:
        ics_file_path = input("Введите путь к файлу .ics: ")

    if os.path.exists(ics_file_path):
        service = authenticate_google_calendar()
        if service:
            print("Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря.")
            add_events_to_google_calendar(service, ics_file_path)
            print("События успешно добавлены в календарь Google.")
        else:
            print("Не удалось выполнить аутентификацию.")
    else:
        print("Указанный файл не существует.")

if __name__ == "__main__":
    main()
