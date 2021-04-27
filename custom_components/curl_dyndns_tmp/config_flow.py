
"""Config flow for CurlDynDNS."""

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL, CONF_URL

from .const import DOMAIN, DEFAULT_INTERVAL_MIN

class CurlDynDnsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CurlDynDNS."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input={}):
        """Handle the initial step."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input:
            return self.async_create_entry(title=user_input.get(CONF_NAME),data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL_MIN): vol.All(
                    vol.Coerce(int)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)
