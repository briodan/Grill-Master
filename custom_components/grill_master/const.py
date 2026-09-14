"""Constants for the Grill Master integration."""

from __future__ import annotations

DOMAIN = "grill_master"
PLATFORMS = ["sensor", "binary_sensor", "climate", "switch", "number"]

# Config keys
CONF_HOST = "host"
CONF_POLL_INTERVAL = "poll_interval"
CONF_CLOUD_ENABLED = "cloud_enabled"
CONF_CLOUD_URL = "cloud_url"

# Defaults
DEFAULT_NAME = "Grill Master"
DEFAULT_POLL_INTERVAL = 5  # seconds
DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_CLOUD_URL = ""

# MCU payload prefixes
STATUS_PREFIX = "FE0B"
TEMP_PREFIX = "FE0C"

# MCU command hex codes (Control Board 8 - Black Label series)
CMD_POWER_OFF = "FE0102FF"
CMD_LIGHT_ON = "FE0201FF"
CMD_LIGHT_OFF = "FE0200FF"
CMD_PRIMER_ON = "FE0801FF"
CMD_PRIMER_OFF = "FE0800FF"
CMD_SET_CELSIUS = "FE0902FF"
CMD_SET_FAHRENHEIT = "FE0901FF"

# Temperature limits (LG1000BL Black Label)
MIN_TEMP_F = 180
MAX_TEMP_F = 600
TEMP_STEP_F = 5

# Probe 1 target (done) temperature bounds. Not hardware-enforced - the LBL
# control board accepts any 3-digit value - these are a sane UI range for a
# meat probe alarm.
PROBE_TARGET_MIN_F = 32
PROBE_TARGET_MAX_F = 210
PROBE_TARGET_STEP_F = 1

# Config data keys
CONF_MAC = "mac"
CONF_DEVICE_ID = "device_id"

# Grill model info
MODEL = "LG1000BL"
MANUFACTURER = "Grill Master"

# DHCP discovery - Espressif OUI used by the ESP32 controller
# MAC format from Sys.GetInfo is "943CC6AABBCC" (no separators)
ESPRESSIF_OUI = "94:3C:C6"
