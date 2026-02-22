URL_QUERY = "https://www.nyurban.com/?page_id=400&filter_id=1&gametypeid=1"

ORGANIZATION = "new_york_urban"
ORG_DISPLAY_NAME = "New York Urban"
FILEPATH_LOG = f"log/{ORGANIZATION}/log_{{date}}.txt"
LOGGER_NAME = f"{ORGANIZATION}_logger"

AJAX_URL = "https://www.nyurban.com/wp-admin/admin-ajax.php"
AJAX_ACTION = "my_open_play_contentbb"
AJAX_GAMETYPE_ID = 1

AJAX_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": URL_QUERY,
    "User-Agent": "Mozilla/5.0",
}

VENUES = [
    {"buttonid": 1, "filterid": 35, "name": "LaGuardia/Fri"},
    {"buttonid": 2, "filterid": 34, "name": "Beacon/Fri"},
    {"buttonid": 3, "filterid": 6, "name": "Brandeis/Fri"},
    {"buttonid": 4, "filterid": 18, "name": "Brandeis/Sunday"},
    {"buttonid": 5, "filterid": 32, "name": "Clinics"},
]
