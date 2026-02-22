import logging
import urllib.request
import urllib.parse
from datetime import datetime as dt

import pandas as pd
from bs4 import BeautifulSoup

from src.scrapers.new_york_urban import new_york_urban_config as nyu_config

logger = logging.getLogger(nyu_config.LOGGER_NAME)


def fetch_venue_html(venue: dict) -> str:
    params = urllib.parse.urlencode({
        "action": nyu_config.AJAX_ACTION,
        "buttonid": venue["buttonid"],
        "gametypeid": nyu_config.AJAX_GAMETYPE_ID,
        "filterid": venue["filterid"],
    })
    req = urllib.request.Request(
        nyu_config.AJAX_URL,
        data=params.encode(),
        headers=nyu_config.AJAX_HEADERS,
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode()


def get_event_info(event_element) -> dict:
    event_info = event_element.find_all("td")
    date = dt.strptime(event_info[1].text.strip(), "%a %m/%d").replace(year=dt.now().year)
    start_datetime = (
        dt.strptime(event_info[4].text.strip().split(" - ")[0], f"%I:%M %p")
        .replace(year=date.year, month=date.month, day=date.day)
    )
    if start_datetime < dt.now():
        start_datetime = start_datetime.replace(date.year + 1)
    end_datetime = (
        dt.strptime(event_info[4].text.strip().split(" - ")[1], f"%I:%M %p")
        .replace(year=start_datetime.year, month=start_datetime.month, day=start_datetime.day)
    )
    return {
        "organization": nyu_config.ORG_DISPLAY_NAME,
        "event_id": event_info[0].find("input", {"type": "checkbox"})["id"],
        "location": event_info[2].text.strip(),
        "start_time": start_datetime,
        "end_time": end_datetime,
        "level": event_info[3].text.strip(),
        "status": event_info[6].text.strip(),
        "price": event_info[5].text.strip(),
        "url": nyu_config.URL_QUERY,
        "date_found": dt.now()
    }


def get_events() -> list[dict]:
    logger.info("Getting events...")
    events = []
    for venue in nyu_config.VENUES:
        html = fetch_venue_html(venue)
        if "NO OPEN SESSION" in html:
            logger.info(f"No events at venue {venue['name']}.")
            continue
        soup = BeautifulSoup(html, "html.parser")
        event_rows = soup.find_all("tr")[1:]
        venue_event_count = 0
        for event_row in event_rows:
            try:
                events.append(get_event_info(event_row))
                venue_event_count += 1
                logger.debug(f"Retrieved event ID {events[-1]['event_id']}.")
            except Exception as e:
                logger.exception(f"Exception raised when collecting event info for venue {venue['name']}: {e}")
        logger.info(f"Retrieved event info for {venue_event_count} events at venue {venue['name']}.")
    logger.info(f"Retrieved event info for {len(events)} events.")
    return events


def remove_full_events(events: list) -> list:
    logger.info("Removing full events...")
    num_total_events = len(events)
    i = 0
    while i < len(events):
        if events[i]["status"] == "Sold Out":
            logger.debug(f"Event ID {events.pop(i)['event_id']} removed.")
        else:
            i += 1
    logger.info(f"{num_total_events - len(events)} of {num_total_events} removed. {len(events)} remaining.")
    return events


def remove_seen_events(new_events: list, df_existing_events: pd.DataFrame):
    logger.info("Removing seen events...")
    num_total_events = len(new_events)
    set_existing_events = set(
        df_existing_events.apply(lambda x: (x["start_time"].to_pydatetime(), x["location"], x["level"]), axis=1)
    )
    i = 0
    while i < len(new_events):
        if (new_events[i]["start_time"], new_events[i]["location"], new_events[i]["level"]) in set_existing_events:
            logger.debug(f"Event ID {new_events.pop(i)['event_id']} removed.")
        else:
            i += 1
    logger.info(f"{num_total_events - len(new_events)} of {num_total_events} removed. {len(new_events)} remaining.")
    return new_events


def remove_beginner_events(events: list):
    logger.info("Removing beginner events...")
    num_total_events = len(events)
    i = 0
    while i < len(events):
        if "Beg" in events[i]["level"]:
            logger.debug(f"Event ID {events.pop(i)['event_id']} removed.")
        else:
            i += 1
    logger.info(f"{num_total_events - len(events)} of {num_total_events} removed. {len(events)} remaining.")
    return events
