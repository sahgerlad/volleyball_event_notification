import logging
import time
from datetime import datetime as dt

from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from src import config
from src.scrapers.new_york_urban import new_york_urban_config as nyu_config

logger = logging.getLogger(__name__)


def load_query_results_page(driver, url: str) -> None:
    logger.debug(f"Loading {nyu_config.ORG_DISPLAY_NAME} query page: {url}...")
    driver.get(url)
    time.sleep(config.SLEEP_TIME_PAGE_LOAD)
    logger.debug(f"{nyu_config.ORG_DISPLAY_NAME} query page loaded.")


def get_event_info(event_element) -> dict:
    event_info = event_element.find_all("td")
    date = dt.strptime(event_info[1].text.strip(), "%a %m/%d").replace(year=dt.now().year)
    if date < dt.now():
        date = date.replace(date.year + 1)
    start_datetime = (
        dt.strptime(event_info[4].text.strip().split(" - ")[0], f"%I:%M %p")
        .replace(year=date.year, month=date.month, day=date.day)
    )
    end_datetime = (
        dt.strptime(event_info[4].text.strip().split(" - ")[1], f"%I:%M %p")
        .replace(year=date.year, month=date.month, day=date.day)
    )
    return {
        "organization": nyu_config.ORG_DISPLAY_NAME,
        "event_id": event_info[0].find("input", {"type": "checkbox"})["id"],
        "location": event_info[2].text.strip(),
        "start_time": start_datetime,
        "end_time": end_datetime,
        "level": event_info[3].text.strip().split(" ")[0],
        "status": event_info[6].text.strip(),
        "price": event_info[5].text.strip(),
        "url": nyu_config.URL_QUERY,
        "date_found": dt.now()
    }


def get_events(driver, url: str) -> list[dict]:
    load_query_results_page(driver, url)
    venue_elements = driver.find_elements(By.CSS_SELECTOR, "div.register_bbtab a")
    events = []
    for venue_element in venue_elements:
        venue_element.click()
        time.sleep(config.SLEEP_TIME_ELEMENT_LOAD)
        if driver.find_elements(By.XPATH, "//*[contains(text(), '!! NO OPEN SESSION AVAILABLE !!')]"):
            continue
        table_element = driver.find_element(By.XPATH, "//table[.//th[contains(text(), 'Date')]]")
        soup = BeautifulSoup(table_element.get_attribute("outerHTML"), "html.parser")
        event_rows = soup.find_all("tr")[1:]
        for event_row in event_rows:
            try:
                events.append(get_event_info(event_row))
            except Exception as e:
                logger.exception(f"Exception raised when collecting event info for venue {venue_element.text}: {e}")
    return events


def remove_full_events(events: list) -> list:
    i = 0
    while i < len(events):
        if events[i]["status"] == "Sold Out":
            events.pop(i)
        else:
            i += 1
    return events


def remove_seen_events(new_events: list, existing_event_ids: list):
    i = 0
    while i < len(new_events):
        if new_events[i]["event_id"] in existing_event_ids:
            new_events.pop(i)
        else:
            i += 1
    return new_events


def remove_beginner_events(new_events: list):
    i = 0
    while i < len(new_events):
        if "Beg" in new_events[i]["level"]:
            new_events.pop(i)
        else:
            i += 1
    return new_events
