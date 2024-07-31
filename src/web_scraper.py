import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

def start_browser():
    logger.info("Starting browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    logger.info("Browser started.")
    return driver


def get_query_element(driver, url):
    driver.get(url)
    # Add delay for page to fully load
    time.sleep(5)
    query_element = (
        driver.find_element(By.CSS_SELECTOR, "main")
        .find_element(By.CSS_SELECTOR, "div")
        .find_element(By.CSS_SELECTOR, "div")
        .find_elements(By.CSS_SELECTOR, "div")[22]
        .find_elements(By.CSS_SELECTOR, "div")[358]
        .find_element(By.CSS_SELECTOR, "div")
        .find_elements(By.CSS_SELECTOR, "div")[80]
    )
    return query_element


def get_event_elements(query_element):
    event_elements = query_element.find_elements(By.XPATH, "./*")
    idx = 0
    while idx != len(event_elements):
        if len(event_elements[idx].find_elements(By.CSS_SELECTOR, "div")) == 1:
            event_elements.pop(idx)
        else:
            idx += 1
    return event_elements[:-1]


def get_event_ids(driver, url):
    logger.info(f"Getting event IDs from url: {url}...")
    query_element = get_query_element(driver, url)
    event_elements = get_event_elements(query_element)
    event_ids = []
    for idx in range(len(event_elements)):
        event_elements[idx].click()
        time.sleep(1)
        event_ids.append(driver.current_url.split("/")[-1])
        query_element = get_query_element(driver, url)
        event_elements = get_event_elements(query_element)
    logger.info(f"Retrieved event IDs: {event_ids}")
    return event_ids



