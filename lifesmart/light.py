"""Support for LifeSmart Gateway Light."""
import binascii
import logging
import struct
import urllib.request
import json
import time
import hashlib
import aiohttp
from homeassistant.components.light import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGB_COLOR,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_COLOR_TEMP,
    # SUPPORT_BRIGHTNESS,
    # SUPPORT_COLOR,
    LightEntity,
    ENTITY_ID_FORMAT,
)
import homeassistant.util.color as color_util

from . import LifeSmartDevice

_LOGGER = logging.getLogger(__name__)

QUANTUM_TYPES = [
    "OD_WE_QUAN",
]

SPOT_TYPES = ["MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT"]

LIGHT_DIMMER_TYPES = [
    "SL_LI_WW",
]

MAX_MIREDS = int(1000000 / 2700)
MIN_MIREDS = int(1000000 / 6500)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for LifeSmart devices."""
    if discovery_info is None:
        return
    dev = discovery_info.get("dev")
    param = discovery_info.get("param")
    devices = []

    # P1,P2,P3 info packed into one data for one entity
    if dev["devtype"] in LIGHT_DIMMER_TYPES:
        devices.append(LifeSmartLight(dev, "P1P2", dev["data"], param))
    else:
        for idx in dev["data"]:
            if idx in [
                "RGB",
                "RGBW",
                "dark",
                "dark1",
                "dark2",
                "dark3",
                "bright",
                "bright1",
                "bright2",
                "bright3",
            ]:
                devices.append(LifeSmartLight(dev, idx, dev["data"][idx], param))
    async_add_entities(devices)


async def asyncPOST(url, data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            r = await response.text()
            return r


class LifeSmartLight(LifeSmartDevice, LightEntity):
    """Representation of a LifeSmartLight."""

    def __init__(self, dev, idx, val, param):
        """Initialize the LifeSmartLight."""
        super().__init__(dev, idx, val, param)
        self._brightness = None
        self._color_temp = None

        self.entity_id = ENTITY_ID_FORMAT.format(
            (
                dev["devtype"] + "_" + dev["agt"][:-3] + "_" + dev["me"] + "_" + idx
            ).lower()
        )
        _LOGGER.info("light: %s added..", str(self.entity_id))
        _LOGGER.info("light: idx: %s ", str(idx))
        _LOGGER.info("light: val: %s ", str(val))

        if dev["devtype"] in LIGHT_DIMMER_TYPES:
            self._color_mode = ColorMode.COLOR_TEMP
            self._supported_color_modes = {ColorMode.COLOR_TEMP}
            self._max_mireds = MAX_MIREDS
            self._min_mireds = MIN_MIREDS
            for data_idx in val:
                if data_idx == "P1":
                    # set on/off
                    if val[data_idx]["type"] % 2 == 1:
                        self._state = True
                    else:
                        self._state = False
                    # set brightness
                    self._brightness = val[data_idx]["val"]
                elif data_idx == "P2":
                    # set color temp
                    ratio = 1 - (val[data_idx]["val"] / 255)
                    self._color_temp = (
                        int((self._max_mireds - self._min_mireds) * ratio)
                        + self._min_mireds
                    )
        else:
            # _LOGGER.info("light: param: %s ", str(param))
            if val["type"] % 2 == 1:
                self._state = True
            else:
                self._state = False

            if idx == "P1":
                self._color_mode = ColorMode.COLOR_TEMP
                self._supported_color_modes = {ColorMode.COLOR_TEMP}
            elif idx in ["HS"]:
                self._color_mode = ColorMode.HS
                self._supported_color_modes = {ColorMode.HS}
            elif idx in ["RGBW", "RGB"]:
                self._color_mode = ColorMode.RGBW
                self._supported_color_modes = {ColorMode.RGBW}
            else:
                self._color_mode = ColorMode.ONOFF
                self._supported_color_modes = {ColorMode.ONOFF}

            value = val["val"]
            if idx in ["HS"]:
                if value == 0:
                    self._hs = None
                else:
                    rgbhexstr = "%x" % value
                    rgbhexstr = rgbhexstr.zfill(8)
                    rgbhex = bytes.fromhex(rgbhexstr)
                    rgba = struct.unpack("BBBB", rgbhex)
                    rgb = rgba[1:]
                    self._hs = color_util.color_RGB_to_hs(*rgb)
                    _LOGGER.info("hs: %s", str(self._hs))
            elif idx in ["RGB_0"]:
                if value == 0:
                    self._rgb_color = None
                else:
                    rgbhexstr = "%x" % value
                    rgbhexstr = rgbhexstr.zfill(8)
                    rgbhex = bytes.fromhex(rgbhexstr)
                    rgba = struct.unpack("BBBB", rgbhex)
                    self._rgb_color = rgba[1:]
                    _LOGGER.info("rgb: %s", str(self._rgb_color))
            elif idx in ["RGBW", "RGB"]:
                rgbhexstr = "%x" % value
                rgbhexstr = rgbhexstr.zfill(8)
                rgbhex = bytes.fromhex(rgbhexstr)
                rgbhex = struct.unpack("BBBB", rgbhex)
                # convert from wrgb to rgbw tuple
                self._rgbw_color = rgbhex[1:] + (rgbhex[0],)
                _LOGGER.info("rgbw: %s", str(self._rgbw_color))

    async def async_added_to_hass(self):
        if self._devtype not in SPOT_TYPES:
            return
        rmdata = {}
        rmlist = await LifeSmartLight._lifesmart_GetRemoteList(self)
        for ai in rmlist:
            rms = await LifeSmartLight._lifesmart_GetRemotes(self, ai)
            rms["category"] = rmlist[ai]["category"]
            rms["brand"] = rmlist[ai]["brand"]
            rmdata[ai] = rms
        self._attributes.setdefault("remotelist", rmdata)

    @property
    def is_on(self):
        """Return true if it is on."""
        return self._state

    @property
    def hs_color(self):
        """Return the hs color value."""
        return self._hs

    @property
    def rgbw_color(self):
        """Return the rgbw_color color value."""
        return self._rgbw_color

    @property
    def rgb_color(self):
        """Return the rgb_color color value."""
        return self._rgb_color

    @property
    def brightness(self):
        """Return the brightness value."""
        return self._brightness

    @property
    def color_temp(self):
        """Return the color_temp value."""
        return self._color_temp

    @property
    def max_mireds(self):
        """Return the max_mireds value."""
        return self._max_mireds

    @property
    def min_mireds(self):
        """Return the min_mireds value."""
        return self._min_mireds

    # @property
    # def supported_features(self):
    #    """Return the supported features."""
    #    return SUPPORT_COLOR + SUPPORT_BRIGHTNESS

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return self._color_mode

    @property
    def supported_color_modes(self):
        """Return the color mode of the light."""
        return self._supported_color_modes

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if self._devtype in LIGHT_DIMMER_TYPES:
            if ATTR_BRIGHTNESS in kwargs:
                if (
                    await super().async_lifesmart_epset(
                        self, "0xcf", kwargs[ATTR_BRIGHTNESS], "P1"
                    )
                    == 0
                ):
                    self._brightness = kwargs[ATTR_BRIGHTNESS]
                    self.async_schedule_update_ha_state()
            if ATTR_COLOR_TEMP in kwargs:
                ratio = (kwargs[ATTR_COLOR_TEMP] - self._min_mireds) / (
                    self._max_mireds - self._min_mireds
                )
                val = int((-ratio + 1) * 255)
                if await super().async_lifesmart_epset(self, "0xcf", val, "P2") == 0:
                    self._color_temp = kwargs[ATTR_COLOR_TEMP]
                    self.async_schedule_update_ha_state()
            if await super().async_lifesmart_epset(self, "0x81", 1, "P1") == 0:
                self._state = True
                self.async_schedule_update_ha_state()

        else:
            if self.color_mode == ColorMode.HS:
                if ATTR_HS_COLOR in kwargs:
                    self._hs = kwargs[ATTR_HS_COLOR]

                rgb = color_util.color_hs_to_RGB(*self._hs)
                rgba = (0,) + rgb
                rgbhex = binascii.hexlify(struct.pack("BBBB", *rgba)).decode("ASCII")
                rgbhex = int(rgbhex, 16)

                if (
                    await super().async_lifesmart_epset(self, "0xff", rgbhex, self._idx)
                    == 0
                ):
                    self._state = True
                    self.async_schedule_update_ha_state()

            if self.color_mode == ColorMode.RGB:
                if ATTR_RGB_COLOR in kwargs:
                    self._rgb_color = kwargs[ATTR_RGB_COLOR]
                # convert rgb to wrgb tuple
                rgbhex = (0,) + self._rgb_color
                rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode("ASCII")
                rgbhex = int(rgbhex, 16)

                if (
                    await super().async_lifesmart_epset(self, "0xff", rgbhex, self._idx)
                    == 0
                ):
                    self._state = True
                    self.async_schedule_update_ha_state()

            if self.color_mode == ColorMode.RGBW:
                if ATTR_RGBW_COLOR in kwargs:
                    self._rgbw_color = kwargs[ATTR_RGBW_COLOR]
                    # convert rgbw to wrgb tuple
                    rgbhex = (self._rgbw_color[-1],) + self._rgbw_color[:-1]
                    rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode(
                        "ASCII"
                    )
                    rgbhex = int(rgbhex, 16)

                    if (
                        await super().async_lifesmart_epset(
                            self, "0xff", rgbhex, self._idx
                        )
                        == 0
                    ):
                        self._state = True
                        self.async_schedule_update_ha_state()
                else:
                    if (
                        await super().async_lifesmart_epset(self, "0x81", 1, self._idx)
                        == 0
                    ):
                        self._state = True
                        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        if self._devtype in LIGHT_DIMMER_TYPES:
            if await super().async_lifesmart_epset(self, "0x80", 0, "P1") == 0:
                self._state = False
                self.async_schedule_update_ha_state()

        elif self._devtype in SPOT_TYPES:
            if ATTR_RGBW_COLOR in kwargs:
                self._rgbw_color = kwargs[ATTR_RGBW_COLOR]
                # convert rgbw to wrgb tuple
                rgbhex = (self._rgbw_color[-1],) + self._rgbw_color[:-1]
                rgbhex = binascii.hexlify(struct.pack("BBBB", *rgbhex)).decode("ASCII")
                rgbhex = int(rgbhex, 16)

                if (
                    await super().async_lifesmart_epset(self, "0xfe", rgbhex, self._idx)
                    == 0
                ):
                    self._state = False
                    self.async_schedule_update_ha_state()
            else:
                if await super().async_lifesmart_epset(self, "0x80", 0, self._idx) == 0:
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

    @staticmethod
    async def _lifesmart_GetRemoteList(self):
        appkey = self._appkey
        apptoken = self._apptoken
        usertoken = self._usertoken
        userid = self._userid
        agt = self._agt
        url = "https://api.us.ilifesmart.com/app/irapi.GetRemoteList"
        tick = int(time.time())
        sdata = (
            "method:GetRemoteList,agt:"
            + agt
            + ",time:"
            + str(tick)
            + ",userid:"
            + userid
            + ",usertoken:"
            + usertoken
            + ",appkey:"
            + appkey
            + ",apptoken:"
            + apptoken
        )
        sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()
        send_values = {
            "id": 1,
            "method": "GetRemoteList",
            "params": {"agt": agt},
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": userid,
                "appkey": appkey,
                "time": tick,
                "sign": sign,
            },
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        _LOGGER.info("_lifesmart_GetRemoteList send_data -- " + str(send_data))
        # req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
        # response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        response = json.loads(await asyncPOST(url, send_data, header))
        # _LOGGER.info("_lifesmart_GetRemoteList -- " + str(response))
        return response["message"]

    @staticmethod
    async def _lifesmart_GetRemotes(self, ai):
        appkey = self._appkey
        apptoken = self._apptoken
        usertoken = self._usertoken
        userid = self._userid
        agt = self._agt
        url = "https://api.us.ilifesmart.com/app/irapi.GetRemote"
        tick = int(time.time())
        sdata = (
            "method:GetRemote,agt:"
            + agt
            + ",ai:"
            + ai
            + ",needKeys:2,time:"
            + str(tick)
            + ",userid:"
            + userid
            + ",usertoken:"
            + usertoken
            + ",appkey:"
            + appkey
            + ",apptoken:"
            + apptoken
        )
        sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()
        send_values = {
            "id": 1,
            "method": "GetRemote",
            "params": {"agt": agt, "ai": ai, "needKeys": 2},
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": userid,
                "appkey": appkey,
                "time": tick,
                "sign": sign,
            },
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        # req = urllib.request.Request(url=url, data=send_data.encode('utf-8'), headers=header, method='POST')
        # response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        response = json.loads(await asyncPOST(url, send_data, header))
        # _LOGGER.info("_lifesmart_GetRemotes -- " + str(response))
        return response["message"]["codes"]
