"""Constants for Curl DynDNS."""

# Base component constants
DOMAIN = "curl_dyndns"
DEFAULT_INTERVAL_MIN = 15
IPIFY_TIMEOUT_SEC = 20
DNS_TIMEOUT_SEC = 30
VERSION = "0.0.1"
REQUIRED_FILES = [
    ".translations/en.json",
    "const.py",
    "config_flow.py",
    "manifest.json",
]
