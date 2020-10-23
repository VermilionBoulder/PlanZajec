import requests
from lxml import etree
import re
import datetime
import Event

DEFAULT_URLS = {'two_weeks': "http://planzajec.uek.krakow.pl/index.php?typ=G&id=184251&okres=1",
                'semester': "http://planzajec.uek.krakow.pl/index.php?typ=G&id=184251&okres=2"}


class PlanGetter:
    def __init__(self, plan_urls=DEFAULT_URLS):
        self.r = None
        self.plan_urls = plan_urls

    def get_plan(self, plan_scope: str):
        self.r = requests.get(self.plan_urls[plan_scope])
        self.r.encoding = self.r.apparent_encoding
        page_source = self.r.text
        page_source = page_source.encode(encoding=self.r.encoding)
        page_source = page_source.decode(encoding="UTF-8")
        page_source = str(page_source.split('\n'))
        table = etree.HTML(page_source).find("body/table")
        rows = iter(table)
        _ = [col.text for col in next(rows)]
        # rows = next(rows)
        events = []
        for row in rows:
            values = [col.text for col in row]
            start_end_times = re.findall(r"\d\d:\d\d", values[1])
            start = datetime.datetime.strptime(f"{values[0]} {start_end_times[0]}", "%Y-%m-%d %H:%M")
            end = datetime.datetime.strptime(f"{values[0]} {start_end_times[1]}", "%Y-%m-%d %H:%M")
            event_type = '[Wkł]' if values[3] == "wykład zdalny" else '[Ćw.]'
            summary = f"{event_type} {values[2]}"
            description = f"Prowadzący: {values[4]}"
            events.append(Event.Event(start, end, summary, description).get_calendar_event())
        return events
