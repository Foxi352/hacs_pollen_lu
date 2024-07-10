from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import ServiceCall, SupportsResponse

from datetime import timedelta, datetime
import logging
import aiohttp

from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config) -> bool:
    """Set up the integration."""
    _LOGGER.debug("async_setup()")

    return True

async def async_setup_entry(hass, entry) -> bool:
    """Set up the integration from a config entry."""
    _LOGGER.debug("async_setup_entry()")
    session = aiohttp.ClientSession()
    coordinator = MyCoordinator(hass, entry, session)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )
    # Ensure we add the update listener only once
    if not entry.update_listeners:
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        
    # Launche the force_poll service call
    async def handle_force_poll_service(call: ServiceCall) -> dict:
        """Handle the force_poll service call."""
        success = await coordinator.async_force_poll()
        _LOGGER.debug(f"Force poll result: {success}")
        hass.states.async_set("pollen_lu.force_poll", success)
        return success
        
    # Register the force_poll service if not already registered
    if not hass.services.has_service(DOMAIN, 'force_poll'):
        hass.services.async_register(DOMAIN, 'force_poll', handle_force_poll_service,supports_response=SupportsResponse.ONLY)

    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry()")
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
        if unload_ok:
            coordinator = hass.data[DOMAIN].pop(entry.entry_id)
            await coordinator.session.close()
            return True
        return False
    _LOGGER.warning(f"Attempted to unload entry {entry.entry_id} that was not loaded.")
    return False

async def async_reload_entry(hass, entry):
    """Reload config entry when options are updated."""
    _LOGGER.debug("async_reload_entry()")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

class MyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, session):
        """Initialize the coordinator."""
        self.session = session
        self.entry = entry
        self.translations = None
        self.pollen = None
        self.last_poll = None
        self.next_poll = None

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 60))
        update_interval = timedelta(minutes=scan_interval)
        _LOGGER.info(f"Polling pollen.lu API every {scan_interval} minutes")

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
 
    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        headers = {
            "Host": "pollen-api.chl.lu",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Sec-Fetch-Site": "cross-site",
            "Origin": "capacitor://localhost",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Accept-Language": "lb,en-GB;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "empty",
            "Connection": "keep-alive",
        }
        _LOGGER.debug("Fetching translation and pollen data from API")
        success = True
        try:
            async with self.session.get(f"{API_URL}/translations", headers=headers) as response:
                self.translations = await response.json()
                self.translations = self.translations["data"]
                _LOGGER.debug("Translations fetched")
        except Exception as err:
            _LOGGER.error(f"Error fetching translations: {err}")
            success = False
            raise UpdateFailed(f"Error fetching translations: {err}")
        try:
            async with self.session.get(f"{API_URL}/pollens", headers=headers) as response:
                self.pollen = await response.json()
                self.pollen = self.pollen["data"]
                self.last_poll = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
                self.next_poll = (datetime.now().astimezone() + self.update_interval).strftime("%Y-%m-%d %H:%M:%S")
                _LOGGER.debug("Pollen fetched")
        except Exception as err:
            _LOGGER.error(f"Error fetching pollen counts: {err}")
            success = False
            raise UpdateFailed(f"Error fetching pollen counts: {err}")
            
        return {"success": success}

    async def async_force_poll(self) -> dict:
        """Handle the service call to force poll the API."""
        _LOGGER.debug("Force poll service called")
        success = await self._async_update_data()
        return success