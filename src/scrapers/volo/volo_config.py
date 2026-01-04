import os

URL_ACCOUNT_LOGIN = "https://www.volosports.com/login"
URL_QUERY_TEST = "https://www.volosports.com/discover?cityName=New%20York%20Metro%20Area&view=SPORTS&subView=DAILY&programTypes%5B%5D=PICKUP&sportNames%5B%5D=Volleyball"
URL_QUERY = "https://www.volosports.com/discover?cityName=New%20York%20Metro%20Area&view=SPORTS&subView=DAILY&sportNames%5B0%5D=Volleyball&programTypes%5B0%5D=PICKUP&venueIds%5B0%5D=33402bdd-9775-4048-a8bb-45e991828ccb&venueIds%5B1%5D=c1c5bae2-654e-4f58-81f6-825d6cbdf5d3&venueIds%5B2%5D=b6443f56-7157-41e1-8804-faded173e515&venueIds%5B3%5D=82dbb9a7-9ef0-4ec5-9e50-5b9c2836c633&venueIds%5B4%5D=799824d3-2224-4174-833c-561da318e867"

ORGANIZATION = "volo"
ORG_DISPLAY_NAME = "Volo"
FILEPATH_LOG = f"log/{ORGANIZATION}/log_{{date}}.txt"
LOGGER_NAME = f"{ORGANIZATION}_logger"

USERNAME = os.environ.get("VOLO_USERNAME")
PASSWORD = os.environ.get("VOLO_PASSWORD")

SIGNUP_NOTICE = 1 * 24 * 60 * 60
