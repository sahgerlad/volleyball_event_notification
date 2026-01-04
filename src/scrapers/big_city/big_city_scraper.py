import logging
from datetime import datetime as dt

import pandas as pd

from src import config
from src.scrapers.big_city import big_city_config as bc_config

logger = logging.getLogger(bc_config.LOGGER_NAME)


async def load_query_results_page(page, url: str) -> None:
    logger.debug(f"Loading {bc_config.ORG_DISPLAY_NAME} query page: {url}...")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    iframe = page.frame_locator("iframe[src*='opensports.net']")
    while True:
        load_more_button = iframe.locator("xpath=//span[text()='Load More']")
        if await load_more_button.count() == 0:
            break
        await load_more_button.first.click()
        await page.wait_for_timeout(config.SLEEP_TIME_URL_LOAD)
    logger.debug(f"{bc_config.ORG_DISPLAY_NAME} query page loaded.")
    return iframe


async def get_event_info(event_locator) -> dict:
    url = await event_locator.locator("a").first.get_attribute("href")
    event_id = url.split("/")[4].split("?")[0]
    event_text = await event_locator.inner_text()
    event_details = event_text.split("\n")
    status = "Available"
    if event_details[0] in ["Filled", "Upcoming"]:
        status = event_details.pop(0)
    if event_details[0] in ["A", "BB", "All Skill Levels"]:
        event_details.pop(0)
    level = event_details.pop(0).split(" ")[0]
    event_times = event_details.pop(0).split(" - ")
    try:
        start_datetime = dt.strptime(event_times[0], "%b %d, %Y %I:%M %p")
    except ValueError:
        start_datetime = dt.strptime(event_times[0], "%b %d %I:%M %p").replace(year=dt.now().year)
        if start_datetime.date() < dt.now().date():
            start_datetime = start_datetime.replace(year=start_datetime.year + 1)
    if len(event_times[1].split(" ")) > 2:
        event_times[1] = " ".join(event_times[1].split(" ")[:2])
    end_datetime = dt.strptime(event_times[1], "%I:%M %p")
    end_datetime = \
        dt(start_datetime.year, start_datetime.month, start_datetime.day, end_datetime.hour, end_datetime.minute)
    location = event_details.pop(0)
    price = None
    if event_details:
        price = event_details.pop(0)
    return {
        "organization": bc_config.ORG_DISPLAY_NAME,
        "event_id": event_id,
        "location": location,
        "start_time": start_datetime,
        "end_time": end_datetime,
        "level": level,
        "status": status,
        "price": price.strip("$") if isinstance(price, str) and "$" in price else price,
        "url": url,
        "date_found": dt.now()
    }


async def get_registration_datetime(page, url: str) -> dt:
    logger.debug(f"Getting registration date on url: {url}...")
    context = page.context
    new_page = await context.new_page()
    try:
        await new_page.goto(url)
        await new_page.wait_for_load_state("networkidle")
        reg_element = new_page.locator("xpath=//span[contains(text(), 'Registration starts')]")
        reg_text = await reg_element.inner_text()
        reg_datetime = (
            dt
            .strptime(reg_text, "Registration starts %b %d %I:%M %p")
            .replace(year=dt.now().year)
        )
        if reg_datetime.date() < dt.now().date():
            reg_datetime = reg_datetime.replace(year=reg_datetime.year + 1)
        logger.debug(f"Found registration date: {reg_datetime}")
    except Exception as e:
        logger.exception(f"Exception raised when collecting the registration datetime on url {url}: {e}")
        reg_datetime = None
    finally:
        await new_page.close()
    return reg_datetime


async def get_events(page, url: str) -> list[dict]:
    logger.info(f"Getting events...")
    iframe = await load_query_results_page(page, url)
    events = []
    cards_container = iframe.locator('[class*="Games_cardsContainer"]')
    event_elements = cards_container.locator("> *")
    count = await event_elements.count()
    for i in range(count):
        try:
            event_locator = event_elements.nth(i)
            event_info = await get_event_info(event_locator)
            events.append(event_info)
            logger.debug(f"Retrieved event ID {events[-1]['event_id']}.")
        except Exception as e:
            logger.exception(f"Exception raised when collecting event info for index {i}: {e}")
    for event_info in events:
        if event_info["status"] == "Upcoming":
            event_info["registration_date"] = await get_registration_datetime(page, event_info["url"])
    logger.info(f"Retrieved event info for {len(events)} events.")
    return events


def remove_seen_events(new_events: list[dict], df_existing_events: pd.DataFrame):
    logger.info("Removing seen events...")
    num_total_events = len(new_events)
    i = 0
    while i < len(new_events):
        event_id = new_events[i]["event_id"]
        status = new_events[i]["status"]
        if len(
            df_existing_events[
                (df_existing_events["event_id"] == event_id) &
                ((df_existing_events["status"] == status) | (df_existing_events["status"].isin(["Available", "Filled"])))
            ]
        ):
            logger.debug(f"Event ID {new_events.pop(i)['event_id']} removed.")
        else:
            i += 1
    logger.info(f"{num_total_events - len(new_events)} of {num_total_events} removed. {len(new_events)} remaining.")
    return new_events


def keep_advanced_events(events: list[dict]):
    logger.info("Keeping only advanced events...")
    num_total_events = len(events)
    i = 0
    while i < len(events):
        if events[i]["level"] != "Advanced":
            logger.debug(f"Event ID {events.pop(i)['event_id']} removed.")
        else:
            i += 1
    logger.info(f"{num_total_events - len(events)} of {num_total_events} removed. {len(events)} remaining.")
    return events
