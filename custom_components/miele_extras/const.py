"""Konstanter for Miele Extras."""

DOMAIN = "miele_extras"
CONF_REFRESH_TOKEN = "refresh_token"

# Miele@mobile app-API (privat; den officielle 3rd-party API har ikke disse funktioner)
TOKEN_URL = "https://prod.map.miele-iot.com/dk/token"
API_BASE = "https://rest-eu.domestic.miele-iot.com"
CLIENT_ID = "com.miele.app.consumer"
UA_AUTH = "Miele/26015058 CFNetwork/3860.700.2 Darwin/25.6.0"
UA_API = "Miele@mobile 4.19.0 iOS"

# Den officielle Miele-integration: vores enheder knyttes til dens via via_device
MIELE_DOMAIN = "miele"

UPDATE_INTERVAL_MIN = 15
MIN_IMAGE_INTERVAL = 20  # sekunder mellem kamerabilleder
