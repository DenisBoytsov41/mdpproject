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
    �������� ��� ������ � Google ����������.
    """

    def __init__(self, credentials_file='credentials.json', redirect_uri='http://localhost:8080'):
        """
        ������������� ��������� Google ���������.

        ���������:
            credentials_file (str): ���� � ����� � �������� �������.
            redirect_uri (str): URI ��������������� ��� ��������������.
        """
        self.credentials_file = credentials_file
        self.redirect_uri = redirect_uri

    async def authenticate_telegram(self, bot: Bot, update: Update):
        """
        �������������� ����� Telegram � ��������� ������� � Google ���������.

        ���������:
            bot (Bot): ��������� ���� Telegram.
            update (Update): ���������� Telegram.

        ����������:
            service: ������ Google ���������.
        """
        # �������� ������ ������� ������
        with open(self.credentials_file, 'r') as f:
            cred_data = json.load(f)
            installed_data = cred_data['installed']

        # ������������� ������� Google OAuth2
        client = aioauth_client.GoogleClient(
            client_id=installed_data['client_id'],
            client_secret=installed_data['client_secret'],
            redirect_uri=self.redirect_uri,
            scope='https://www.googleapis.com/auth/calendar'
        )
        authorization_url = client.get_authorize_url()

        if not authorization_url.startswith('https://'):
            raise ValueError("authorization_url ������ ���������� � https://")

        # �������� ��������� ������������ Telegram � �������� �� �����������
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='��������������', url=authorization_url)]
        ])
        user_id = update.message.chat_id if update.message else None
        if not user_id and update.callback_query:
            user_id = update.callback_query.message.chat.id
        await bot.send_message(user_id, '����������, ������� �� ������ ����, ����� ��������������:', reply_markup=keyboard)

        # �������� ������ ������������ � ����� �����������
        authorization_code = None
        while not authorization_code:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.redirect_uri) as response:
                    if response.status == 200:
                        authorization_code = await response.text()
                        break
            await asyncio.sleep(1)

        # ��������� ������ ������� � �������� ������� Google ���������
        access_token, expires_in = await client.get_access_token(code=authorization_code)
        credentials = Credentials(access_token)
        service = build('calendar', 'v3', credentials=credentials)
        return service

    async def add_events_from_ics(self, service, ics_file_path: str):
        """
        ���������� ������� �� ����� ������� .ics � Google ���������.

        ���������:
            service: ������ Google ���������.
            ics_file_path (str): ���� � ����� .ics.

        ����������:
            bool: ������� �� ��������� ������� � ���������.
        """
        if not os.path.exists(ics_file_path):
            print("��������� ���� �� ����������.")
            return False

        # ������ ������� �� ����� .ics � ���������� �� � ���������
        with open(ics_file_path, 'rb') as f:
            calendar = Calendar.from_ical(f.read())

        new_calendar = {
            'summary': '����� ���������',
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

            print("������� ������� ��������� � ����� ��������� Google.")

        return True

    def parse_rrule_string(self, rrule_string: str):
        """
        ������ ������ ������� ���������� ������� (RRULE) �� ������� .ics.

        ���������:
            rrule_string (str): ������ ������� ����������.

        ����������:
            list: ������ ����� � ��������� ���������� �������.
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
