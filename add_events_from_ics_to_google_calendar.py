import asyncio
import http
import os
import socketserver
import ssl
import ssl as ssllib
import sys
import threading
import urllib
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from icalendar import Calendar
from datetime import datetime, timedelta
from telegram import Bot
import re
from telegram import Update
import json
import asyncio
import http.server
import socketserver
import urllib.parse
from ssl import SSLContext

CLIENT_SECRETS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost:8080/'
PORT = 8080
authorization_response = None

async def send_telegram_message(bot, chat_id, messages):
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(chat_id, text=message_text[i:i+max_message_length])

def parse_rrule_string(rrule_string):
    freq_match = re.search(r"'FREQ': \['(.*?)'\]", rrule_string)
    until_match = re.search(r"'UNTIL': \[datetime.datetime\((.*?)\)\]", rrule_string)
    interval_match = re.search(r"'INTERVAL': \[(.*?)\]", rrule_string)

    freq = freq_match.group(1) if freq_match else None
    until = datetime.strptime(until_match.group(1), "%Y, %m, %d, %H, %M") if until_match else None
    interval = int(interval_match.group(1)) if interval_match else None

    until_str = until.strftime('%Y%m%dT%H%M%SZ') if until else None

    recurrence = []
    if freq and until_str and interval:
        recurrence.append(f'RRULE:FREQ={freq};UNTIL={until_str};INTERVAL={interval}')

    return recurrence

def add_events_to_google_calendar(service, ics_file_path):
    with open(ics_file_path, 'rb') as f:
        calendar = Calendar.from_ical(f.read())

    new_calendar = {
        'summary': 'Новый Календарь',
        'timeZone': 'Europe/Moscow'
    }
    created_calendar = service.calendars().insert(body=new_calendar).execute()
    calendar_id = created_calendar['id']

    for event in calendar.walk('VEVENT'):
        event_summary = str(event.get('summary', ''))
        event_description = str(event.get('description', ''))
        event_location = str(event.get('location', ''))
        event_rrule = str(event.get('rrule', ''))

        event_start = event.get('dtstart').dt if event.get('dtstart') else None
        event_end = event.get('dtend').dt if event.get('dtend') else None

        if event_start and event_end:
            event_start_formatted = event_start.strftime('%Y-%m-%dT%H:%M:%S')
            event_end_formatted = event_end.strftime('%Y-%m-%dT%H:%M:%S')

            event_body = {
                'summary': event_summary,
                'description': event_description,
                'location': event_location,
                'start': {'dateTime': event_start_formatted, 'timeZone': 'Europe/Moscow'},
                'end': {'dateTime': event_end_formatted, 'timeZone': 'Europe/Moscow'}
            }
            if event_rrule:
                event_body['recurrence'] = parse_rrule_string(event_rrule)
            #print(event_body)
            service.events().insert(calendarId=calendar_id, body=event_body).execute()

    print("События успешно добавлены в новый календарь Google.")

async def authenticate_google_calendar():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

    webbrowser.open(authorization_url)

    threading.Thread(target=start_local_server).start()

    while not authorization_response:
        await asyncio.sleep(1)

    flow.fetch_token(authorization_response=authorization_response)

    service = build('calendar', 'v3', credentials=flow.credentials)

    return service

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global authorization_response
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        authorization_response = params.get('code', [''])[0]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body>Authorization successful. You can close this tab now.</body></html>')
def get_ssl_context(certfile, keyfile):
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(certfile, keyfile)
    context.set_ciphers("@SECLEVEL=1:ALL")
    return context
def start_local_server():
    server_address = ('localhost', PORT)
    httpd = http.server.HTTPServer(server_address, MyHandler)
    context = get_ssl_context("cert.pem", "key.pem")
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"Local server started at port {PORT}")
    httpd.serve_forever()


async def main():
    subprocess_ics_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    if subprocess_ics_file_path:
        ics_file_path = subprocess_ics_file_path
    else:
        ics_file_path = input("Введите путь к файлу .ics: ")
    update_data_str = sys.argv[2] if len(sys.argv) > 2 else None
    bot_context = sys.argv[3] if len(sys.argv) > 3 else None
    update = None
    bot = None
    if update_data_str is not None:
        update_data = json.loads(update_data_str)
        update = Update.de_json(update_data, None)
    if bot_context is not None:
        bot = Bot(token=bot_context)
        await bot.initialize()
    if os.path.exists(ics_file_path):
        service = await authenticate_google_calendar()
        if service:
            print("Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря.")
            add_events_to_google_calendar(service, ics_file_path)
            print("События успешно добавлены в календарь Google.")
        else:
            print("Не удалось выполнить аутентификацию.")
    else:
        print("Указанный файл не существует.")

if __name__ == "__main__":
    asyncio.run(main())
