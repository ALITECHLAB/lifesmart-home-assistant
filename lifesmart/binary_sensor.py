"""Support for LifeSmart binary sensors."""
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    ENTITY_ID_FORMAT,
)

from . import LifeSmartDevice

_LOGGER = logging.getLogger(__name__)


GUARD_SENSOR = ["SL_SC_G", "SL_SC_BG"]
MOTION_SENSOR = ["SL_SC_MHW", "SL_SC_BM", "SL_SC_CM"]
SMOKE_SENSOR = ["SL_P_A"]


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for lifesmart devices."""
    if discovery_info is None:
        return
    dev = discovery_info.get("dev")
    param = discovery_info.get("param")
    devices = []
    for idx in dev["data"]:
        if idx in ["M", "G", "B", "AXS", "P1"]:
            devices.append(LifeSmartBinarySensor(dev, idx, dev["data"][idx], param))
    async_add_entities(devices)


class LifeSmartBinarySensor(LifeSmartDevice, BinarySensorEntity):
    """Representation of LifeSmartBinarySensor."""

    def __init__(self, dev, idx, val, param):
        super().__init__(dev, idx, val, param)
        self.entity_id = ENTITY_ID_FORMAT.format(
            (
                dev["devtype"] + "_" + dev["agt"][:-3] + "_" + dev["me"] + "_" + idx
            ).lower()
        )
        devtype = dev["devtype"]
        if devtype in GUARD_SENSOR:
            if idx in ["G"]:
                self._device_class = "door"
                if val["val"] == 0:
                    self._state = True
                else:
                    self._state = False
            if idx in ["AXS"]:
                self._device_class = "vibration"
                if val["val"] == 0:
                    self._state = False
                else:
                    self._state = True
            if idx in ["B"]:
                self._device_class = None
                if val["val"] == 0:
                    self._state = False
                else:
                    self._state = True
        elif devtype in MOTION_SENSOR:
            self._device_class = "motion"
            if val["val"] == 0:
                self._state = False
            else:
                self._state = True
        else:
            self._device_class = "smoke"
            if val["val"] == 0:
                self._state = False
            else:
                self._state = True

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._device_class

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id
