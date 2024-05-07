import os
import tkinter as tk
from tkinter import filedialog
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from icalendar import Calendar
from datetime import datetime, timedelta

def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = None

    if os.path.exists('token.json'):
        os.remove('token.json')

    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    return build('calendar', 'v3', credentials=creds)

def choose_ics_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("iCalendar files", "*.ics")])
    return file_path

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
    ics_file_path = choose_ics_file()
    if ics_file_path:
        service = authenticate_google_calendar()
        add_events_to_google_calendar(service, ics_file_path)
        print("События успешно добавлены в календарь Google.")

if __name__ == "__main__":
    main()
