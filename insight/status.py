import time
from db import status


def is_status_valid():
    """
    Check whether the latest status report is valid,
    which means (1) no error and (2) it's up-to-date
    :return: Bool
    """
    s = status.get_latest_status()
    # we check if the timestamp is within an hour
    timestamp_now = int(time.time())
    valid_time = timestamp_now - s['timestamp'] <= 3700  # an hour + 100 sec
    # then check if there was any error
    no_error = s['error'] is None

    return no_error and valid_time


def all_timestamp():
    return list(map(lambda x: x['timestamp'], status.get_all_status()))
