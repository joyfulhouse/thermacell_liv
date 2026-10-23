"""Constants for the Thermacell LIV integration."""

DOMAIN = "thermacell_liv"

# Config entry keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# System status values
STATUS_OFF = "Off"
STATUS_WARMING_UP = "Warming Up"
STATUS_PROTECTED = "Protected"
STATUS_NOT_CONNECTED = "Not Connected"
STATUS_UNKNOWN = "Unknown"

# Connectivity status values
CONNECTIVITY_CONNECTED = "Connected"
CONNECTIVITY_DISCONNECTED = "Disconnected"

# Default values
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 300
# LAN control is experimental (unverified on physical hubs), so it is opt-in.
DEFAULT_PREFER_LOCAL = False

# Values sent to the existing pythermacell reset_refill API.
REFILL_TYPES = {"40 Hour - Yellow Cap": 0, "100 Hour - Blue Cap": 1, "180 Hour - Gray Cap": 2}
