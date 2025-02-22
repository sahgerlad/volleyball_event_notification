import logging
import os
import datetime as dt
import asyncio
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src import event_log, emailer, config
from src.scrapers.volo import volo_scraper, volo_config


def create_logger(path_log):
    os.makedirs(os.path.dirname(path_log), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(path_log)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def start_browser(logger, headless=True):
    logger.info("Starting browser...")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    logger.info("Browser started.")
    return driver


def main_volo(url, filepath_event):
    logger = create_logger(volo_config.FILEPATH_LOG.format(date=dt.date.today().strftime("%Y-%m-%d")))
    logger.info(f"Starting Volo scraper on {url}...")
    try:
        driver = start_browser(logger)
        account_login = volo_scraper.login_to_account(
            driver,
            volo_config.URL_ACCOUNT_LOGIN,
            volo_config.USERNAME,
            volo_config.PASSWORD
        )
        existing_event_ids = event_log.read_event_ids(filepath_event)
        new_events = volo_scraper.get_events(driver, url, account_login, existing_event_ids)
        if not new_events:
            logger.info("No new open event IDs.")
        else:
            event_log.write_event_ids(filepath_event, [event["event_id"] for event in new_events])
            emailer.send_email(**emailer.create_email_content_events(new_events))
        driver.quit()
        retry_counter["volo"] = 0
        logger.info(f"Volo webscrape completed successfully.")
    except Exception as e:
        retry_counter["volo"] += 1
        logger.warning(f"Execution failed. Incrementing retry counter: {retry_counter}")
        logger.exception(e)
        if retry_counter == config.RETRY_LIMIT:
            logger.fatal("Retry limit exceeded.")
            emailer.send_email(**emailer.create_email_content_job_failure(e))


async def main():
    scrapers = [
        ("volo", main_volo, volo_config.URL_QUERY, volo_config.FILEPATH_EVENT_LOG)
    ]
    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(executor, func, url, log) for name, func, url, log in scrapers]
        await asyncio.gather(*tasks)
        await asyncio.sleep(config.SLEEP_TIME)


if __name__ == "__main__":
    retry_counter = {"volo": 0}
    asyncio.run(main())
