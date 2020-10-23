from __future__ import print_function
import PlanGetter
import pickle
import os.path
import datetime
import itertools
import Event
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

DEFAULT_SCOPES = ['https://www.googleapis.com/auth/calendar']
DEFAULT_CALENDAR_ID = 'ss7hkmbme430fqd5h4r8389b7g@group.calendar.google.com'
DEFAULT_TIME_OFFSET = datetime.timedelta(days=14)
EMPTY_EVENT = Event.Event("", "", "", "")


class CalendarApp:
    def __init__(self, scopes=None,
                 calendar_id=DEFAULT_CALENDAR_ID,
                 time_offset=DEFAULT_TIME_OFFSET):
        if scopes is None:
            scopes = DEFAULT_SCOPES
        self.plan = None
        self.creds = None
        self.service = None
        self.scopes = scopes
        self.calendar_id = calendar_id
        self.time_offset = time_offset
        self.plan_getter = PlanGetter.PlanGetter()
        self.plan = None

        self.get_credentials()

    def get_credentials(self):
        """
        Defines self.creds and self.service.
        Called upon initialization.
        :return: None
        """
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('calendar', 'v3', credentials=self.creds)

        # calendar_list_entry = service.calendarList().get(calendarId=CALENDAR_ID).execute()
        # print(calendar_list_entry['Summary'])
        page_token = None
        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            # print(calendar_list['items'])
            # for calendar_list_entry in calendar_list['items']:
            #     print(calendar_list_entry)
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    def insert_events(self, plan_scope: str):
        """
        Inserts events from the specified scope
        into the calendar.
        :param plan_scope:
        :return:
        """
        events = self.plan_getter.get_plan(plan_scope)
        for event in events:
            self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            print(f"Event created: {event.get('summary')}")

    def update_events(self):
        """
        Not yet finished
        This function will run every day, refreshing the
        upcoming two weeks of events in the calendar.
        """
        current_time = datetime.datetime.utcnow()
        current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        now = current_time.isoformat() + 'Z'
        now_plus_two_weeks = (current_time + self.time_offset).isoformat() + 'Z'
        calendar_events = self.service.events().list(calendarId=self.calendar_id,
                                                     singleEvents=True, timeMin=now,
                                                     timeMax=now_plus_two_weeks,
                                                     orderBy='startTime').execute()
        plan_events = self.plan_getter.get_plan('two_weeks')
        calendar_events = calendar_events.get('items', [])

        for p, c in itertools.zip_longest(plan_events, calendar_events, fillvalue=EMPTY_EVENT):
            print(f"Summary: {p['summary'] == c['summary']}")

    def delete_all_events(self):
        """
        Deletes all google calendar events.
        :return: None
        """
        print('Getting all events for deletion')
        events_result = self.service.events().list(calendarId=self.calendar_id,
                                                   singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_id = event['id']
            print(f"Deleting: {start} {event['summary']}...")
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()

    def print_upcoming_two_weeks(self):
        """
        Prints every event between now and two weeks in the future.
        :return: None
        """
        current_time = datetime.datetime.utcnow()
        now = current_time.isoformat() + 'Z'
        now_plus_two_weeks = (current_time + self.time_offset).isoformat() + 'Z'
        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId=self.calendar_id,
                                                   singleEvents=True, timeMin=now,
                                                   timeMax=now_plus_two_weeks,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
