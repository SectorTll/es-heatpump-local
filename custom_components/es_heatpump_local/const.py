"""Constants for the ES Heatpump Local integration."""

DOMAIN = "es_heatpump_local"
PLATFORMS = ["sensor"]

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 18899

FRAME_MAGIC = b"\xAA\x55\x01"
FRAME_END = 0x3A

FRAME_TYPE_SHORT = 1
FRAME_TYPE_LONG = 2

SHORT_SENSOR_COUNT = 45
LONG_SENSOR_COUNT = 136

DEVICE_NAME = "ES Heatpump Local"
DEVICE_MANUFACTURER = "Energy Save"
DEVICE_MODEL = "RS232 Local Bridge"
