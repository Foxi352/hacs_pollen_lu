import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_NAME
from homeassistant.core import callback
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL
)

DEFAULT_CONF_NAME = "Pollen.lu"

class PollenLuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollen LU."""

    VERSION = 2
    MINOR_VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._scan_interval = 60
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_NAME, 
                    default=DEFAULT_CONF_NAME
                    ): str
            }),
            errors=self._errors,
            description_placeholders={"description": "Set the polling interval for fetching data."},
        )

    async def async_step_import(self, user_input=None):
        """Handle import from YAML."""
        return await self.async_step_user(user_input)

    @staticmethod
    #@callback
    def async_get_options_flow(config_entry):
        return PollenLuOptionsFlowHandler(config_entry)

class PollenLuOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Pollen LU."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_SCAN_INTERVAL, 
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, 
                    DEFAULT_SCAN_INTERVAL)
                    ): int
            }),
        )