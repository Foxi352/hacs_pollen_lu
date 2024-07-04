import asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    # Wait for the initial data fetching to complete
    while coordinator.pollen is None or coordinator.translations is None:
        await asyncio.sleep(1) 
    sensors = []
    for pollen in coordinator.pollen:
        if pollen["active"]:
            sensors.append(PollenSensor(coordinator, pollen))
    async_add_entities(sensors)

class PollenSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    
    def __init__(self, coordinator, pollen):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_type = pollen.get("translationKey")
        self._attr_unique_id = f"{pollen.get("id")}_{self.entity_type}"
        self.entity_id = f"sensor.pollen_{self.entity_type}"
        self._attr_native_unit_of_measurement = "p/m³"
        self._attr_icon = "mdi:flower-pollen"
        self._attr_device_class = None
        self._attr_entity_picture = pollen.get("pictures", [])[0].get("path", "")
        self._attr_extra_state_attributes = {}

    def translate(self, key, domain):
        language = self.hass.config.language
        translations = next((item for item in self.coordinator.translations if item["key"] == key and item["domain"] == domain), None)
        if translations:
            translation = next((item for item in translations.get("translations") if item["locale"] == language), None)
        if translation:
            return translation.get("content")
        else:
            return key

    @property
    def name(self):
        """Name of the entity."""
        return f"Pollen {self.translate(self.entity_type, "pollen")}"

    @property
    def state(self):
        """Return the state of the sensor."""
        pollen = next((item for item in self.coordinator.pollen if item["translationKey"] == self.entity_type and item["active"]), None)
        if pollen is not None:
            level = pollen.get("level","")
            if level != "undetected":
                value = round(pollen.get("value"))
            else:
                value = 0
            return value
        else:
            return -1

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        pollen = next((item for item in self.coordinator.pollen if item["translationKey"] == self.entity_type and item["active"]), None)
        thresholds = pollen.get("threshold", None)
        attributes["level"] = pollen.get("level","")
        attributes["last_update"] = pollen.get("lastMeasurementDate")
        attributes["last_poll"] = self.coordinator.last_poll
        attributes["next_poll"] = self.coordinator.next_poll
        attributes["description"] = self.translate(pollen.get("descriptions", [])[0],"pollen")
        if thresholds:
            medium = next((item for item in thresholds if item["type"] == "medium"), None)
            high = next((item for item in thresholds if item["type"] == "high"), None)
            attributes["moderate_threshold"] = medium.get("min", 999)
            attributes["high_threshold"] = high.get("min", 999)
        return attributes

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
