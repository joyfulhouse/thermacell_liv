"""Constants for the Thermacell LIV integration."""

DOMAIN = "thermacell_liv"

# Config entry keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# System status values
STATUS_ERROR = "Error"
STATUS_OFF = "Off"
STATUS_WARMING_UP = "Warming Up"
STATUS_PROTECTED = "Protected"
STATUS_NOT_CONNECTED = "Not Connected"
STATUS_UNKNOWN = "Unknown"

# Connectivity status values
CONNECTIVITY_CONNECTED = "Connected"
CONNECTIVITY_DISCONNECTED = "Disconnected"

# Some hubs constantly report error bit 24 (0x01000000 = 16777216) while fully
# functional, which pinned the status sensor on "Error" (#17). Ignore that bit
# when deciding whether the hub is faulted; any other bit still counts.
BENIGN_ERROR_BITS = 0x01000000

# Default values
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 300
