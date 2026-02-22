import json
import logging
import os

import pandas as pd

from src import config

logger = logging.getLogger(config.LOGGER_NAME)


def read_local_events(file_path) -> pd.DataFrame:
    logger.info(f"Reading local events from {file_path}...")
    if os.path.exists(file_path):
        df_events = pd.read_csv(file_path, parse_dates=["start_time", "end_time"])
    else:
        df_events = pd.DataFrame({
            "organization": [],
            "event_id": [],
            "status": [],
            "start_time": [],
            "end_time": []
        })
        df_events = df_events.astype({
            "organization": str,
            "event_id": str,
            "status": str,
            "start_time": "datetime64[ns]",
            "end_time": "datetime64[ns]"
        })
    logger.info(f"Retrieved {len(df_events)} event IDs.")
    return df_events


def write_events(file_path: str, df_events: pd.DataFrame) -> None:
    logger.info(f"Writing events to {file_path}...")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df_events.to_csv(file_path, index=False)
    logger.info(f"{len(df_events)} events written.")
    return


def concat_dfs(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    all_columns = set(df1.columns).union(set(df2.columns))
    df1 = df1.reindex(columns=list(all_columns))
    df2 = df2.reindex(columns=list(all_columns))
    return pd.concat([df1, df2], ignore_index=True)


def read_retry_counter(file_path: str, default_organizations: dict) -> dict:
    logger.info(f"Reading retry counter from {file_path}...")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                retry_counter = json.load(f)
            logger.info(f"Retrieved retry counter: {retry_counter}")
            return retry_counter
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read retry counter file: {e}. Using defaults.")
    else:
        logger.info("Retry counter file not found. Using defaults.")
    return default_organizations.copy()


def write_retry_counter(file_path: str, retry_counter: dict) -> None:
    logger.info(f"Writing retry counter to {file_path}...")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(retry_counter, f, indent=2)
    logger.info(f"Retry counter written: {retry_counter}")
    return
