import requests
from lxml import etree
import re
import datetime
import Event
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

URL = "http://planzajec.uek.krakow.pl/index.php?typ=G&id=184251&okres=1"
TIMEZONE = "Europe/Warsaw"

class PlanGetter:
    def __init__(self):
        self.r = None


    def get_plan():
        r = requests.get(URL)
        r.encoding = r.apparent_encoding
        page_source = r.text
        page_source = page_source.encode(encoding=r.encoding)
        page_source = page_source.decode(encoding="UTF-8")
        page_source = str(page_source.split('\n'))
        table = etree.HTML(page_source).find("body/table")
        rows = iter(table)
        headers = [col.text for col in next(rows)]
        events = []
        for row in rows:
            values = [col.text for col in row]
            start_end_times = re.findall(r"\d\d:\d\d", values[1])
            start = datetime.datetime.strptime(f"{values[0]} {start_end_times[0]}", "%Y-%m-%d %H:%M")
            end = datetime.datetime.strptime(f"{values[0]} {start_end_times[1]}", "%Y-%m-%d %H:%M")
            type = '[Wkł]' if values[3] == "wykład zdalny" else '[Ćw.]'
            summary = f"{type} {values[2]}"
            description = f"Prowadzący: {values[4]}"

            events.append(Event(start, end, summary, description))

            # print(f"[{type}] {summary} n\From {start} till {end} n\Lecturer: {description}")
            # event = (dict(zip(headers, values)))
        return events
