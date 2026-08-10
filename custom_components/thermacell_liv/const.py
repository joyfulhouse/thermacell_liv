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

# Some hubs constantly report benign bit 0x01000000 while fully functional
# (#17). Firmware 5.4.1 also transiently sets benign bit 0x00000008 during
# warm-up (#17 follow-up). Ignore both when deciding whether the hub is faulted.
BENIGN_ERROR_BITS = 0x01000008

# Default values
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 300
