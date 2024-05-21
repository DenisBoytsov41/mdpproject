import aioauth_client
import aiohttp
import asyncio
import json
import os
import re
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from icalendar import Calendar
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup

class GoogleCalendarManager:
    """
    Менеджер для работы с Google Календарем.
    """

    def __init__(self, credentials_file='credentials.json', redirect_uri='http://localhost:8080'):
        """
        Инициализация менеджера Google Календаря.

        Аргументы:
            credentials_file (str): Путь к файлу с учетными данными.
            redirect_uri (str): URI перенаправления для аутентификации.
        """
        self.credentials_file = credentials_file
        self.redirect_uri = redirect_uri

    async def authenticate_telegram(self, bot: Bot, update: Update):
        """
        Аутентификация через Telegram и получение доступа к Google Календарю.

        Аргументы:
            bot (Bot): Экземпляр бота Telegram.
            update (Update): Обновление Telegram.

        Возвращает:
            service: Сервис Google Календаря.
        """
        # Загрузка данных учетной записи
        with open(self.credentials_file, 'r') as f:
            cred_data = json.load(f)
            installed_data = cred_data['installed']

        # Инициализация клиента Google OAuth2
        client = aioauth_client.GoogleClient(
            client_id=installed_data['client_id'],
            client_secret=installed_data['client_secret'],
            redirect_uri=self.redirect_uri,
            scope='https://www.googleapis.com/auth/calendar'
        )
        authorization_url = client.get_authorize_url()

        if not authorization_url.startswith('https://'):
            raise ValueError("authorization_url должен начинаться с https://")

        # Отправка сообщения пользователю Telegram с запросом на авторизацию
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Авторизоваться', url=authorization_url)]
        ])
        user_id = update.message.chat_id if update.message else None
        if not user_id and update.callback_query:
            user_id = update.callback_query.message.chat.id
        await bot.send_message(user_id, 'Пожалуйста, нажмите на кнопку ниже, чтобы авторизоваться:', reply_markup=keyboard)

        # Ожидание ответа пользователя с кодом авторизации
        authorization_code = None
        while not authorization_code:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.redirect_uri) as response:
                    if response.status == 200:
                        authorization_code = await response.text()
                        break
            await asyncio.sleep(1)

        # Получение токена доступа и создание сервиса Google Календаря
        access_token, expires_in = await client.get_access_token(code=authorization_code)
        credentials = Credentials(access_token)
        service = build('calendar', 'v3', credentials=credentials)
        return service

    async def add_events_from_ics(self, service, ics_file_path: str):
        """
        Добавление событий из файла формата .ics в Google Календарь.

        Аргументы:
            service: Сервис Google Календаря.
            ics_file_path (str): Путь к файлу .ics.

        Возвращает:
            bool: Успешно ли добавлены события в календарь.
        """
        if not os.path.exists(ics_file_path):
            print("Указанный файл не существует.")
            return False

        # Чтение событий из файла .ics и добавление их в календарь
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
                    event_body['recurrence'] = self.parse_rrule_string(event_rrule)
                service.events().insert(calendarId=calendar_id, body=event_body).execute()

            print("События успешно добавлены в новый календарь Google.")

        return True

    def parse_rrule_string(self, rrule_string: str):
        """
        Разбор строки правила повторения событий (RRULE) из формата .ics.

        Аргументы:
            rrule_string (str): Строка правила повторения.

        Возвращает:
            list: Список строк с правилами повторения событий.
        """
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
