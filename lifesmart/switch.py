"""lifesmart switch @skyzhishui"""
import subprocess
import urllib.request
import json
import time
import hashlib
import logging
from . import LifeSmartDevice


from homeassistant.components.switch import (
    SwitchEntity,
    ENTITY_ID_FORMAT,
)

_LOGGER = logging.getLogger(__name__)

CON_AI_TYPE_SCENE = 'scene'
CON_AI_TYPE_AIB = 'aib'
CON_AI_TYPE_GROUP = 'grouphw'
CON_AI_TYPES =[
    CON_AI_TYPE_SCENE,
    CON_AI_TYPE_AIB,
    CON_AI_TYPE_GROUP,
]
AI_TYPES = ["ai"]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Find and return lifesmart switches."""
    if discovery_info is None:
        return
    dev = discovery_info.get("dev")
    param = discovery_info.get("param")
    devices = []
    if dev["devtype"] in AI_TYPES:
        devices.append(LifeSmartSwitch(dev, "s", "s", param))
    else:
        for idx in dev["data"]:
            if idx in ["L1", "L2", "L3", "P1", "P2", "P3"]:
                devices.append(LifeSmartSwitch(dev, idx, dev["data"][idx], param))
    async_add_entities(devices)
    return True


class LifeSmartSwitch(LifeSmartDevice, SwitchEntity):
    def __init__(self, dev, idx, val, param):
        """Initialize the switch."""
        super().__init__(dev, idx, val, param)
        self.entity_id = ENTITY_ID_FORMAT.format(
            (
                dev["devtype"] + "_" + dev["agt"][:-3] + "_" + dev["me"] + "_" + idx
            ).lower()
        )
        if dev["devtype"] in AI_TYPES:
            self._state = False
        else:
            if val["type"] % 2 == 1:
                self._state = True
            else:
                self._state = False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""

    def _get_state(self):
        """get lifesmart switch state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        if self._devtype in AI_TYPES:
            if await super().async_lifesmart_sceneset(self, None, None) == 0:
                self._state = True
                self.async_schedule_update_ha_state()
        else:    
            if await super().async_lifesmart_epset(self, "0x81", 1, self._idx) == 0:
                self._state = True
                self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        if self._devtype in AI_TYPES:
            self._state = False
            self.async_schedule_update_ha_state()
        else:
            if await super().async_lifesmart_epset(self, "0x80", 0, self._idx) == 0:
                self._state = False
                self.async_schedule_update_ha_state()

    @property
    def unique_id(self):
        """A unique identifier for this entity."""
        return self.entity_id
