"""Constants for Miele Extras."""

DOMAIN = "miele_extras"
CONF_REFRESH_TOKEN = "refresh_token"

# Miele@mobile app API (private; the official third-party API does not offer these features)
TOKEN_URL = "https://prod.map.miele-iot.com/dk/token"
API_BASE = "https://rest-eu.domestic.miele-iot.com"
CLIENT_ID = "com.miele.app.consumer"
UA_AUTH = "Miele/26015058 CFNetwork/3860.700.2 Darwin/25.6.0"
UA_API = "Miele@mobile 4.19.0 iOS"

# Official Miele integration: our devices are linked to its devices with via_device
MIELE_DOMAIN = "miele"

UPDATE_INTERVAL_MIN = 15
MIN_IMAGE_INTERVAL = 20  # seconds between camera images
