import logging
from datetime import datetime as dt

from src import config
from src.scrapers.volo import volo_config

logger = logging.getLogger(volo_config.LOGGER_NAME)


async def dismiss_popups(page):
    accept_button = page.get_by_role("button", name="Accept All")
    if await accept_button.count() > 0:
        await accept_button.first.click()
        await page.wait_for_timeout(config.SLEEP_TIME_PAGE_LOAD)
    await page.evaluate("""
        () => {
            const modal = document.querySelector('.ab-iam-root');
            if (modal) modal.remove();
            const overlay = document.querySelector('.ab-in-app-message');
            if (overlay) overlay.remove();
        }
    """)
    await page.wait_for_timeout(config.SLEEP_TIME_PAGE_LOAD)


async def login_to_account(context, url, volo_account, volo_password):
    logger.info(f"Logging into {volo_config.ORG_DISPLAY_NAME} account with username {volo_account}: {url}...")
    account_login = False
    login_page = await context.new_page()
    try:
        await login_page.goto(url)
        await login_page.wait_for_load_state("networkidle")
        await dismiss_popups(login_page)
        await login_page.get_by_label("Email").fill(volo_account)
        await login_page.get_by_label("Password").fill(volo_password)
        await login_page.get_by_role("button", name="Log in with email").click()
        await login_page.wait_for_timeout(config.SLEEP_TIME_URL_LOAD)
        if login_page.url == url:
            logger.error(f"Login attempt to {volo_config.ORG_DISPLAY_NAME} account unsuccessful.")
        else:
            account_login = True
            logger.info(f"Login to {volo_config.ORG_DISPLAY_NAME} account successful.")
    except Exception as e:
        logger.exception(f"Error when attempting to log into the {volo_config.ORG_DISPLAY_NAME} account: {e}")
    finally:
        await login_page.close()
    return account_login


async def load_query_results_page(page, url):
    logger.debug(f"Loading {volo_config.ORG_DISPLAY_NAME} query page: {url}...")
    start = dt.now()
    await page.goto(url)
    while True:
        ready_state = await page.evaluate("document.readyState")
        if ready_state == "complete":
            break
        elapsed = (dt.now() - start).total_seconds()
        if elapsed < config.LOAD_PAGE_LIMIT:
            await page.wait_for_timeout(config.SLEEP_TIME_ELEMENT_LOAD)
        else:
            raise RuntimeError(f"Page load exceeded load limit of {config.LOAD_PAGE_LIMIT} seconds.")
    elapsed = (dt.now() - start).total_seconds()
    await page.wait_for_timeout(config.SLEEP_TIME_PAGE_LOAD)
    logger.debug(f"{volo_config.ORG_DISPLAY_NAME} query page loaded in {elapsed} seconds.")


async def get_query_element(page):
    main_element = page.locator("main")
    divs = main_element.locator("div")
    count = await divs.count()
    for i in range(count):
        elem = divs.nth(i)
        text = await elem.inner_text()
        if text.startswith("Pickup") and ":" in text:
            return divs.nth(i - 3)
        elif text.startswith("No results"):
            return elem
    return None


async def get_page_elements(query_element):
    children = query_element.locator("> *")
    last_child = children.last
    page_elements = last_child.locator("xpath=.//div[@tabindex]")
    count = await page_elements.count()
    if count > 2:
        result = []
        for i in range(1, count - 1):
            result.append(page_elements.nth(i))
        return result
    return []


async def refresh_elements(page, url, page_idx, account_login):
    await load_query_results_page(page, url)
    query_element = await get_query_element(page)
    query_text = await query_element.inner_text()
    if "No results" in query_text:
        return None, []
    page_elements = await get_page_elements(query_element)
    if page_idx < len(page_elements):
        await page_elements[page_idx].click()
    await page.wait_for_timeout(config.SLEEP_TIME_ELEMENT_LOAD)
    query_element = await get_query_element(page)
    event_elements = await get_event_elements(query_element, account_login)
    return query_element, event_elements


async def get_event_elements(query_element, account_login: bool):
    children = query_element.locator("> *")
    count = await children.count()
    valid_event_elements = []
    for i in range(count):
        element = children.nth(i)
        text = await element.inner_text()
        # Remove elements that do not contain an event
        if "Pickup" not in text:
            continue
        # Remove full events (need to be logged in to see event capacity)
        if account_login:
            dir_elements = element.locator("xpath=.//div[@dir]")
            dir_count = await dir_elements.count()
            if dir_count > 0:
                capacity_text = await dir_elements.last.inner_text()
                event_capacity = capacity_text.split("/")
                try:
                    if event_capacity[0] == event_capacity[1]:
                        continue
                except IndexError:
                    logger.debug(f"Event capacity could not be found: {capacity_text}")
        valid_event_elements.append(element)
    return valid_event_elements


def parse_event_datetime(str_date, time_range):
    dt_start = dt.strptime(str_date, "%a, %B %d")
    str_start_time, str_end_time = time_range.split(" - ")
    dt_start_time = dt.strptime(str_start_time, "%I:%M%p")
    dt_current = dt.now()
    dt_start = dt_start.replace(year=dt_current.year, hour=dt_start_time.hour, minute=dt_start_time.minute)
    if dt_current > dt_start:
        dt_start = dt_start.replace(year=dt_current.year + 1)
    dt_end_time = dt.strptime(str_end_time, "%I:%M%p")
    dt_end = dt_start.replace(hour=dt_end_time.hour, minute=dt_end_time.minute)
    return dt_start, dt_end


async def get_event_info(page):
    event_id = page.url.split("/")[-1]
    event_details_element = page.locator("[class^='styles_program-detail-item-container']")
    event_text = await event_details_element.inner_text()
    event_details = event_text.split("\n")
    start_datetime, end_datetime = parse_event_datetime(event_details[0], event_details[2])
    location = event_details[3] + ", " + event_details[1]
    level = event_details[4] if len(event_details) >= 5 else None
    return {
        "organization": volo_config.ORG_DISPLAY_NAME,
        "event_id": event_id,
        "location": location,
        "start_time": start_datetime,
        "end_time": end_datetime,
        "level": level,
        "url": f"https://www.volosports.com/d/{event_id}",
        "date_found": dt.now()
    }


async def get_events(page, url: str, account_login: bool, existing_events: list = None) -> list[dict]:
    if existing_events is None:
        existing_events = []
    await load_query_results_page(page, url)
    logger.info(f"Getting events...")
    events = []
    query_element = await get_query_element(page)
    query_text = await query_element.inner_text()
    if "No results" in query_text:
        return events
    page_elements = await get_page_elements(query_element)
    page_idx = 0
    while page_idx < len(page_elements):
        if page_idx == 0:
            event_elements = await get_event_elements(query_element, account_login)
        else:
            _, event_elements = await refresh_elements(page, url, page_idx, account_login)
        logger.info(f"Found {len(event_elements)} open event(s) on page {page_idx + 1}.")
        idx = 0
        while idx < len(event_elements):
            try:
                dir_elements = event_elements[idx].locator("xpath=.//div[@dir]")
                await dir_elements.first.click()
                await page.wait_for_timeout(config.SLEEP_TIME_PAGE_LOAD)
                event_info = await get_event_info(page)
                page_content = await page.content()
                if (
                    event_info["event_id"] in existing_events
                    or any(d["event_id"] == event_info["event_id"] for d in events)
                    or "You are already registered!" in page_content
                ):
                    idx += 1
                    logger.info(
                        f"Found event ID {event_info['event_id']} but event ID is not new."
                    )
                    continue
                registration_confirmed = False
                if (
                    account_login
                    and (event_info["start_time"] - dt.now()).total_seconds() > volo_config.SIGNUP_NOTICE
                    and await check_free_event(page)
                    and not (
                        event_info["start_time"].hour == 18
                        and (event_info["end_time"] - event_info["start_time"]).seconds <= 3600
                    )
                ):
                    registration_confirmed = await event_registration(page)
                event_info["registered"] = registration_confirmed
                logger.info(
                    f"Retrieved event ID {event_info['event_id']} and registration is {'not ' if not registration_confirmed else ''}confirmed."
                )
                events.append(event_info)
                if not registration_confirmed:
                    idx += 1
            except Exception as e:
                logger.exception(f"Exception encountered while collecting event index {idx} on page {page_idx + 1}: {e}")
                idx += 1
                logger.info(f"Index incremented to {idx}")
            finally:
                _, event_elements = await refresh_elements(page, url, page_idx, account_login)
        await load_query_results_page(page, url)
        query_element = await get_query_element(page)
        query_text = await query_element.inner_text()
        if "No results" in query_text:
            break
        page_idx += 1
        page_elements = await get_page_elements(query_element)
    logger.info("Retrieved all event IDs.")
    return events


async def check_free_event(page):
    page_source = await page.content()
    free_event = False
    if "Order Total" in page_source and "$0.00" in page_source[page_source.index("Order Total"):]:
        free_event = True
    return free_event


async def event_registration(page):
    checkbox_elements = page.locator("input[type='checkbox']")
    checkbox_count = await checkbox_elements.count()
    for i in range(checkbox_count):
        await checkbox_elements.nth(i).click()
    register_button = page.locator("xpath=//button[contains(text(), 'Register')]")
    await register_button.click()
    await page.wait_for_timeout(config.SLEEP_TIME_PAGE_LOAD)
    registration_confirmed = False
    confirmation = page.locator("xpath=//*[contains(text(), 'Your spot has been confirmed!')]")
    if await confirmation.count() > 0:
        registration_confirmed = True
    else:
        logger.warning("Attempted to register for event but could not identify confirmation")
    return registration_confirmed
