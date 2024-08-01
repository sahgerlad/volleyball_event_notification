import logging
import os
import csv

logger = logging.getLogger(__name__)

def create_event_log_file(file_path):
    if not os.path.exists(file_path):
        logger.info(f"Creating event log file in {file_path}...")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w"):
            pass
        logger.info("Event log file created.")
    return


def read_event_ids(file_path):
    logger.info(f"Reading event IDs from {file_path}...")
    create_event_log_file(file_path)
    with open(file_path, "r", newline="") as file:
        reader = csv.reader(file)
        event_ids = [row[0] for row in reader]
    logger.info(f"Retrieved event IDs: {event_ids}")
    return event_ids


def write_event_ids(file_path, event_ids):
    logger.info(f"Writing event IDs to {file_path}...")
    create_event_log_file(file_path)
    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file)
        for event_id in set(event_ids):
            writer.writerow([event_id])
    logger.info(f"New event IDs written: {event_ids}")
    return
