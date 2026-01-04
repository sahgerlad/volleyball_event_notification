import os
from dotenv import load_dotenv

load_dotenv()

# Email config
SMTP_PORT = 587
EMAIL_SENDER = "volo.notification@gmail.com"
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# Main config
FILEPATH_LOG = "log/log_{date}.txt"
FILEPATH_EVENT_LOG = "data/event_log.csv"
FILEPATH_RETRY_COUNTER = "data/retry_counter.json"
LOGGER_NAME = "main_logger"
RETRY_LIMIT = 5

# Web scraper config (times in milliseconds for Playwright)
SLEEP_TIME_PAGE_LOAD = 5_000
SLEEP_TIME_URL_LOAD = 1_000
SLEEP_TIME_ELEMENT_LOAD = 1_000
LOAD_PAGE_LIMIT = 30
