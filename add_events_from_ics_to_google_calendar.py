import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from icalendar import Calendar
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRETS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost:8080/'
PORT = 8080

def authenticate_google_calendar():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    credentials = flow.run_local_server()

    service = build('calendar', 'v3', credentials=credentials)

    return service

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    authorization_code = None

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/oauth2callback':
            query = parse_qs(parsed_path.query)
            OAuthCallbackHandler.authorization_code = query['code'][0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Authentication Successful</title></head>')
            self.wfile.write(b'<body><p>Authentication successful! You can close this window now.</p></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
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
        event_start = event.get('dtstart').dt
        event_end = event.get('dtend').dt

        event_start = event_start.strftime('%Y-%m-%dT%H:%M:%S') + '+03:00'
        event_end = event_end.strftime('%Y-%m-%dT%H:%M:%S') + '+03:00'

        event_body = {
            'summary': event_summary,
            'description': event_description,
            'start': {'dateTime': event_start},
            'end': {'dateTime': event_end}
        }

        service.events().insert(calendarId=calendar_id, body=event_body).execute()

    print("События успешно добавлены в новый календарь Google.")

def main():
    subprocess_ics_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    if subprocess_ics_file_path:
        ics_file_path = subprocess_ics_file_path
    else:
        ics_file_path = input("Введите путь к файлу .ics: ")

    if os.path.exists(ics_file_path):
        service = authenticate_google_calendar()
        add_events_to_google_calendar(service, ics_file_path)
        print("События успешно добавлены в календарь Google.")
    else:
        print("Указанный файл не существует.")

if __name__ == "__main__":
    main()
