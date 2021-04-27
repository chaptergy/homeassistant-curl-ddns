"""Integrate with any Dynamic DNS service that allows updates via HTTP requests."""
import asyncio
import logging

import aiohttp
import async_timeout
import voluptuous as vol
from datetime import timedelta

from homeassistant.const import CONF_SCAN_INTERVAL, CONF_URL
from homeassistant.util import get_local_ip
import homeassistant.helpers.config_validation as cv

from .const import DEFAULT_INTERVAL_MIN, DOMAIN, REQUIRED_FILES, TIMEOUT_SEC, VERSION

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL, DOMAIN): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL_MIN): vol.All(
                    vol.Coerce(int), vol.Range(min=5)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(hass, config):
    """Initialize the CurlDynDNS component."""
    conf = config.data

    if not conf:
        _LOGGER.error("Failed to initialize CurlDynDNS: config is not set")
        return False

    url = conf.get(CONF_URL)
    update_interval = timedelta(minutes=conf.get(CONF_SCAN_INTERVAL))

    session = hass.helpers.aiohttp_client.async_get_clientsession()

    result = await _update_ip(hass, session, url)

    if result is False:
        return False

    async def update_ip_callback(now):
        """Update the DNS entry."""
        await _update_ip(hass, session, url)

    hass.helpers.event.async_track_time_interval(
        update_ip_callback, update_interval
    )

    return True


async def _update_ip(hass, session, url):
    """Update DNS entry."""

    if url is None:
        _LOGGER.error("CurlDynDNS update url is empty")
        return False

    v4_in_url = "%ip4%" in url
    v6_in_url = "%ip6%" in url

    if v4_in_url:
        v4_request = asyncio.create_task(get_public_ipv4(session))
    if v6_in_url:
        v6_request = asyncio.create_task(get_public_ipv6(session))

    if v4_in_url:
        v4 = await v4_request
        if v4 is None:
            v4 = ''
        url = url.replace("%ip4%", v4)
    if v6_in_url:
        v6 = await v6_request
        if v6 is None:
            v6 = ''
        url = url.replace("%ip6%", v6)

    try:
        with async_timeout.timeout(TIMEOUT_SEC):
            resp = await session.get(url)
            status = resp.status

            if status == 200:
                # IP has been changed.
                _LOGGER.debug("Updating DNS was successful")
                return True
            else:
                body = await resp.text()
                _LOGGER.error("Updating DNS failed with status %i: %s", status, body)

    except aiohttp.ClientError as err:
        _LOGGER.error("Can't connect to CurlDynDNS url: %s", repr(err))
    except asyncio.TimeoutError:
        _LOGGER.warning("Timeout from CurlDynDNS url %s", url)
    except Exception as err:
        _LOGGER.error("Error during CurlDynDNS update: %s", repr(err))

    return False

async def get_public_ipv4(session):
    try:
        _LOGGER.debug("Fetching public IPv4 address...")
        with async_timeout.timeout(TIMEOUT_SEC):
            resp = await session.get("https://api4.ipify.org/")
            ip = await resp.text()
            _LOGGER.debug("Received public IPv4 address: %s", ip)
            return ip

    except aiohttp.ClientError as err:
        _LOGGER.error("Can't connect CurlDynDNS to ipify.org v4 api: %s", repr(err))
    except asyncio.TimeoutError as err:
        _LOGGER.error("Timeout for CurlDynDNS from ipify.org v4 api: %s", repr(err))
    except Exception as err:
        _LOGGER.error("Error during CurlDynDNS request to ipify.org v6 api: %s", repr(err))
    return None

async def get_public_ipv6(session):
    try:
        _LOGGER.debug("Fetching public IPv6 address...")
        with async_timeout.timeout(TIMEOUT_SEC):
            resp = await session.get("https://api6.ipify.org/")
            ip = await resp.text()
            _LOGGER.debug("Received public IPv6 address: %s", ip)
            return ip

    except aiohttp.ClientError as err:
        if "No address associated with hostname" in str(err):
            _LOGGER.debug("CurlDynDNS could not resolve ipify.org v6 domain, you probably do not have IPv6")
        else:
            _LOGGER.error("Can't connect CurlDynDNS to ipify.org v6 api: %s", repr(err))
    except asyncio.TimeoutError as err:
        _LOGGER.error("Timeout for CurlDynDNS from ipify.org v6 api: %s", repr(err))
    except Exception as err:
        _LOGGER.error("Error during CurlDynDNS request to ipify.org v6 api: %s", repr(err))

    return None