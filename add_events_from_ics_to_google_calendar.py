import http
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import aioauth_client
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from aioauth_client import GoogleClient
from googleapiclient.discovery import build
from icalendar import Calendar
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import re
from telegram import Update
import json
import http.server
import asyncio
import http.server
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pyngrok import ngrok, conf
from config import *
import aiohttp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CLIENT_SECRETS_FILE = 'credentials.json'
authorization_response = None


async def send_telegram_message(bot, chat_id, messages):
    max_message_length = 4096
    message_text = "\n".join(messages)

    if len(message_text) <= max_message_length:
        await bot.send_message(chat_id, text=message_text)
    else:
        for i in range(0, len(message_text), max_message_length):
            await bot.send_message(chat_id, text=message_text[i:i + max_message_length])


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
            service.events().insert(calendarId=calendar_id, body=event_body).execute()

    print("События успешно добавлены в новый календарь Google.")


async def get_authorization_code():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://v2462318.hosted-by-vdsina.ru/oauth/callback/') as response:
            if response.status == 200:
                return await response.text()
            else:
                return None

def parse_authorization_code(callback_url):
    parsed_url = urlparse(callback_url)
    query_params = parse_qs(parsed_url.query)
    authorization_code = query_params.get('code', [None])[0]
    return authorization_code

async def authenticate_google_calendar(bot, update):
    with open(CRED_JSON, 'r') as f:
        cred_data = json.load(f)
        installed_data = cred_data['installed']
    client = GoogleClient(
        client_id=installed_data['client_id'],
        client_secret=installed_data['client_secret'],
        redirect_uri=REDIRECT_URI,
        scope=SCOPES[0]
    )
    authorization_url = client.get_authorize_url()

    if not authorization_url.startswith('https://'):
        raise ValueError("authorization_url должен начинаться с https://")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Авторизоваться', url=authorization_url)]])
    user_id = None
    if update.message is not None:
        user_id = update.message.chat_id
    if user_id is None and update.callback_query is not None:
        user_id = update.callback_query.message.chat.id
    await bot.send_message(user_id, 'Пожалуйста, нажмите на кнопку ниже, чтобы авторизоваться:', reply_markup=keyboard)

    # Ждем ответа пользователя с кодом авторизации через callback
    authorization_code = None
    while not authorization_code:
        async with aiohttp.ClientSession() as session:
            async with session.get(REDIRECT_URI) as response:
                if response.status == 200:
                    authorization_code = await response.text()
                    break
        await asyncio.sleep(1)

    access_token, expires_in = await client.get_access_token(code=authorization_code)
    credentials = Credentials(access_token)
    service = build('calendar', 'v3', credentials=credentials)
    return service


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
        service = await authenticate_google_calendar(bot, update)
        user_id = None
        if update.message is not None:
            user_id = update.message.chat_id
        if user_id is None and update.callback_query is not None:
            user_id = update.callback_query.message.chat.id
        if service:
            await send_telegram_message(bot, user_id, ["Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря."])
            #print("Успешная аутентификация. Теперь вы можете использовать сервис Google Календаря.")
            add_events_to_google_calendar(service, ics_file_path)
            await send_telegram_message(bot, user_id,
                                        ["События успешно добавлены в календарь Google."])
            #print("События успешно добавлены в календарь Google.")
        else:
            await send_telegram_message(bot, user_id,
                                        ["Не удалось выполнить аутентификацию."])
            #print("Не удалось выполнить аутентификацию.")
    else:
        print("Указанный файл не существует.")


if __name__ == "__main__":
    asyncio.run(main())
