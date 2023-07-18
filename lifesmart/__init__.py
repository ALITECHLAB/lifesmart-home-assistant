"""lifesmart by @skyzhishui"""
import subprocess
from unittest import case
import urllib.request
import json
import time
import datetime
import hashlib
import logging
import threading
import websocket
import asyncio
import struct
import aiohttp
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
)
import homeassistant.util.color as color_util

import voluptuous as vol
import sys

sys.setrecursionlimit(100000)

from homeassistant.const import (
    CONF_FRIENDLY_NAME,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_DRY,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_OFF,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.core import callback
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util.dt import utcnow

_LOGGER = logging.getLogger(__name__)

CONF_LIFESMART_APPKEY = "appkey"
CONF_LIFESMART_APPTOKEN = "apptoken"
CONF_LIFESMART_USERTOKEN = "usertoken"
CONF_LIFESMART_USERID = "userid"
CONF_EXCLUDE_ITEMS = "exclude"
CONF_EXCLUDE_AGTS = "exclude_agt"
CONF_AI_INCLUDE_AGTS = "ai_include_agt"
CONF_AI_INCLUDE_ITEMS = "ai_include_me"

CON_AI_TYPE_SCENE = 'scene'
CON_AI_TYPE_AIB = 'aib'
CON_AI_TYPE_GROUP = 'grouphw'
CON_AI_TYPES =[
    CON_AI_TYPE_SCENE,
    CON_AI_TYPE_AIB,
    CON_AI_TYPE_GROUP,
]
AI_TYPES = ["ai"]
SWTICH_TYPES = [
    "OD_WE_OT1",
    "SL_MC_ND1",
    "SL_MC_ND2",
    "SL_MC_ND3",
    "SL_NATURE",
    "SL_OL",
    "SL_OL_3C",
    "SL_OL_DE",
    "SL_OL_UK",
    "SL_OL_UL",
    "SL_OL_W",
    "SL_P_SW",
    "SL_S",
    "SL_SF_IF1",
    "SL_SF_IF2",
    "SL_SF_IF3",
    "SL_SF_RC",
    "SL_SPWM",
    "SL_SW_CP1",
    "SL_SW_CP2",
    "SL_SW_CP3",
    "SL_SW_DM1",
    "SL_SW_FE1",
    "SL_SW_FE2",
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_ND1",
    "SL_SW_ND2",
    "SL_SW_ND3",
    "SL_SW_NS3",
    "SL_SW_RC",
    "SL_SW_RC1",
    "SL_SW_RC2",
    "SL_SW_RC3",
    "SL_SW_NS1",
    "SL_SW_NS2",
    "SL_SW_NS3",
    "V_IND_S",
]
LIGHT_SWITCH_TYPES = [
    "SL_OL_W",
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_CT_RGBW",
]
LIGHT_DIMMER_TYPES = [
    "SL_LI_WW",
]

QUANTUM_TYPES = [
    "OD_WE_QUAN",
]

SPOT_TYPES = ["MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT"]
BINARY_SENSOR_TYPES = [
    "SL_SC_G",
    "SL_SC_BG",
    "SL_SC_MHW ",
    "SL_SC_BM",
    "SL_SC_CM",
    "SL_P_A",
]
COVER_TYPES = ["SL_DOOYA"]
GAS_SENSOR_TYPES = ["SL_SC_WA ", "SL_SC_CH", "SL_SC_CP", "ELIQ_EM"]
EV_SENSOR_TYPES = ["SL_SC_THL", "SL_SC_BE", "SL_SC_CQ"]
OT_SENSOR_TYPES = ["SL_SC_MHW", "SL_SC_BM", "SL_SC_G", "SL_SC_BG"]
LOCK_TYPES = ["SL_LK_LS", "SL_LK_GTM", "SL_LK_AG", "SL_LK_SG", "SL_LK_YL"]
GUARD_SENSOR_TYPES = ["SL_SC_G", "SL_SC_BG"]

LIFESMART_STATE_LIST = [
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_DRY,
]

CLIMATE_TYPES = ["V_AIR_P", "SL_CP_DN"]

ENTITYID = "entity_id"
DOMAIN = "lifesmart"

LifeSmart_STATE_MANAGER = "lifesmart_wss"


async def asyncPOST(url, data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            r = await response.text()
            return r


async def asycn_lifesmart_EpGetAll(appkey, apptoken, usertoken, userid):
    url = "https://api.us.ilifesmart.com/app/api.EpGetAll"
    tick = int(time.time())
    sdata = (
        "method:EpGetAll,time:"
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
        "method": "EpGetAll",
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
    # req = urllib.request.Request(
    #     url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    # )
    # response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    response = json.loads(await asyncPOST(url, send_data, header))
    if response["code"] == 0:
        return response["message"]
    return False

async def asycn_lifesmart_SceneGet(appkey, apptoken, usertoken, userid, agt):
    url = "https://api.us.ilifesmart.com/app/api.SceneGet"
    tick = int(time.time())
    sdata = (
        "method:SceneGet,agt:"
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
        "method": "SceneGet",
        "params": {
            "agt": agt,
        },
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
    # req = urllib.request.Request(
    #     url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    # )
    # response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    response = json.loads(await asyncPOST(url, send_data, header))
    if response["code"] == 0:
        return response["message"]
    return False

def lifesmart_EpGetAll(hass, appkey, apptoken, usertoken, userid):
    url = "https://api.us.ilifesmart.com/app/api.EpGetAll"
    tick = int(time.time())
    sdata = (
        "method:EpGetAll,time:"
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
        "method": "EpGetAll",
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
    req = urllib.request.Request(
        url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    )
    response = json.loads(
        hass.async_add_executor_job(urllib.request.urlopen(req).read().decode("utf-8"))
    )
    # response = json.loads(await asyncPOST(url, send_data, header))
    if response["code"] == 0:
        return response["message"]
    return False


def lifesmart_Sendkeys(
    appkey, apptoken, usertoken, userid, agt, ai, me, category, brand, keys
):
    url = "https://api.us.ilifesmart.com/app/irapi.SendKeys"
    tick = int(time.time())
    # keys = str(keys)
    sdata = (
        "method:SendKeys,agt:"
        + agt
        + ",ai:"
        + ai
        + ",brand:"
        + brand
        + ",category:"
        + category
        + ",keys:"
        + keys
        + ",me:"
        + me
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
    _LOGGER.debug("sendkey: %s", str(sdata))
    send_values = {
        "id": 1,
        "method": "SendKeys",
        "params": {
            "agt": agt,
            "me": me,
            "category": category,
            "brand": brand,
            "ai": ai,
            "keys": keys,
        },
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
    req = urllib.request.Request(
        url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    )
    response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    _LOGGER.debug("sendkey_res: %s", str(response))
    return response


def lifesmart_Sendackeys(
    appkey,
    apptoken,
    usertoken,
    userid,
    agt,
    ai,
    me,
    category,
    brand,
    keys,
    power,
    mode,
    temp,
    wind,
    swing,
):
    url = "https://api.us.ilifesmart.com/app/irapi.SendACKeys"
    tick = int(time.time())
    # keys = str(keys)
    sdata = (
        "method:SendACKeys,agt:"
        + agt
        + ",ai:"
        + ai
        + ",brand:"
        + brand
        + ",category:"
        + category
        + ",keys:"
        + keys
        + ",me:"
        + me
        + ",mode:"
        + str(mode)
        + ",power:"
        + str(power)
        + ",swing:"
        + str(swing)
        + ",temp:"
        + str(temp)
        + ",wind:"
        + str(wind)
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
    _LOGGER.debug("sendackey: %s", str(sdata))
    send_values = {
        "id": 1,
        "method": "SendACKeys",
        "params": {
            "agt": agt,
            "me": me,
            "category": category,
            "brand": brand,
            "ai": ai,
            "keys": keys,
            "power": power,
            "mode": mode,
            "temp": temp,
            "wind": wind,
            "swing": swing,
        },
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
    req = urllib.request.Request(
        url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    )
    response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    _LOGGER.debug("sendackey_res: %s", str(response))
    return response


def lifesmart_SceneSet(appkey, apptoken, usertoken, userid, agt, id):
    url = "https://api.us.ilifesmart.com/app/api.SceneSet"
    tick = int(time.time())
    # keys = str(keys)
    sdata = (
        "method:SceneSet,agt:"
        + agt
        + ",id:"
        + id
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
    _LOGGER.debug("SceneSet: %s", str(sdata))
    send_values = {
        "id": 101,
        "method": "SceneSet",
        "params": {
            "agt": agt,
            "id": id,
        },
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
    req = urllib.request.Request(
        url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    )
    response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    _LOGGER.debug("SceneSet_res: %s", str(response))
    return response


async def async_setup(hass, config):
    """Set up the lifesmart component."""
    param = {}
    param["appkey"] = config[DOMAIN][CONF_LIFESMART_APPKEY]
    param["apptoken"] = config[DOMAIN][CONF_LIFESMART_APPTOKEN]
    param["usertoken"] = config[DOMAIN][CONF_LIFESMART_USERTOKEN]
    param["userid"] = config[DOMAIN][CONF_LIFESMART_USERID]
  
    exclude_items = config[DOMAIN][CONF_EXCLUDE_ITEMS]
    exclude_agts = config[DOMAIN][CONF_EXCLUDE_AGTS]
    ai_include_agts = config[DOMAIN][CONF_AI_INCLUDE_AGTS]
    ai_include_items = config[DOMAIN][CONF_AI_INCLUDE_ITEMS]

    devices = await asycn_lifesmart_EpGetAll(
        param["appkey"],
        param["apptoken"],
        param["usertoken"],
        param["userid"],
    )
    for dev in devices:
        if dev["me"] in exclude_items or dev["agt"] in exclude_agts:
            continue
        devtype = dev["devtype"]
        # dev['agt'] = dev['agt'].replace("_","")
        # dev['agt'] = dev['agt'][:-3]
        if devtype in SWTICH_TYPES:
            discovery.load_platform(
                hass, "switch", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in BINARY_SENSOR_TYPES:
            discovery.load_platform(
                hass, "binary_sensor", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in COVER_TYPES:
            discovery.load_platform(
                hass, "cover", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in SPOT_TYPES:
            discovery.load_platform(
                hass, "light", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in CLIMATE_TYPES:
            discovery.load_platform(
                hass, "climate", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in GAS_SENSOR_TYPES or devtype in EV_SENSOR_TYPES:
            discovery.load_platform(
                hass, "sensor", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in OT_SENSOR_TYPES:
            discovery.load_platform(
                hass, "sensor", DOMAIN, {"dev": dev, "param": param}, config
            )
        if devtype in LIGHT_SWITCH_TYPES or devtype in LIGHT_DIMMER_TYPES:
            discovery.load_platform(
                hass, "light", DOMAIN, {"dev": dev, "param": param}, config
            )
    if ai_include_agts is not False: 
        for agt in ai_include_agts:
            scenes = await asycn_lifesmart_SceneGet(
                param["appkey"],
                param["apptoken"],
                param["usertoken"],
                param["userid"],
                agt,
            )
           
            if scenes is not False: 
                for scene in scenes:
                    if scene['id'] in ai_include_items:
                        devtype = "ai"
                        me = scene['id']
                        dev = { "devtype": devtype, "me": me, "agt": agt }
                        discovery.load_platform(
                            hass, "switch", DOMAIN, {"dev": {**dev, **scene}, "param": param}, config
                        )
                    

    def send_keys(call):
        """Handle the service call."""
        agt = call.data["agt"]
        me = call.data["me"]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        restkey = lifesmart_Sendkeys(
            param["appkey"],
            param["apptoken"],
            param["usertoken"],
            param["userid"],
            agt,
            ai,
            me,
            category,
            brand,
            keys,
        )
        _LOGGER.debug("sendkey: %s", str(restkey))

    def send_ackeys(call):
        """Handle the service call."""
        agt = call.data["agt"]
        me = call.data["me"]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        power = call.data["power"]
        mode = call.data["mode"]
        temp = call.data["temp"]
        wind = call.data["wind"]
        swing = call.data["swing"]
        restackey = lifesmart_Sendackeys(
            param["appkey"],
            param["apptoken"],
            param["usertoken"],
            param["userid"],
            agt,
            ai,
            me,
            category,
            brand,
            keys,
            power,
            mode,
            temp,
            wind,
            swing,
        )
        _LOGGER.debug("sendkey: %s", str(restackey))

    def scene_set(call):
        """Handle the service call."""
        agt = call.data["agt"]
        id = call.data["id"]
        restkey = lifesmart_SceneSet(
            param["appkey"],
            param["apptoken"],
            param["usertoken"],
            param["userid"],
            agt,
            id,
        )
        _LOGGER.debug("scene_set: %s", str(restkey))

    def get_fan_mode(_fanspeed):
        fanmode = None
        if _fanspeed < 30:
            fanmode = FAN_LOW
        elif _fanspeed < 65 and _fanspeed >= 30:
            fanmode = FAN_MEDIUM
        elif _fanspeed >= 65:
            fanmode = FAN_HIGH
        return fanmode

    async def set_Event(msg):
        if (
            msg["msg"]["idx"] != "s"
            and msg["msg"]["me"] not in exclude_items
            and msg["msg"]["agt"] not in exclude_agts
        ):
            devtype = msg["msg"]["devtype"]
            # agt = msg['msg']['agt'].replace("_","")
            agt = msg["msg"]["agt"][:-3]
            if devtype in SWTICH_TYPES and msg["msg"]["idx"] in [
                "L1",
                "L2",
                "L3",
                "P1",
                "P2",
                "P3",
            ]:
                enid = (
                    "switch."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = hass.states.get(enid).attributes
                if msg["msg"]["type"] % 2 == 1:
                    hass.states.set(enid, "on", attrs)
                else:
                    hass.states.set(enid, "off", attrs)
            elif devtype in BINARY_SENSOR_TYPES and msg["msg"]["idx"] in [
                "M",
                "G",
                "B",
                "AXS",
                "P1",
            ]:
                enid = (
                    "binary_sensor."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = hass.states.get(enid).attributes
                if devtype in GUARD_SENSOR_TYPES and msg["msg"]["idx"] in ["G"]:
                    if msg["msg"]["val"] == 0:
                        hass.states.set(enid, "on", attrs)
                    else:
                        hass.states.set(enid, "off", attrs)
                else:
                    if msg["msg"]["val"] == 0:
                        hass.states.set(enid, "off", attrs)
                    else:
                        hass.states.set(enid, "on", attrs)

            elif devtype in COVER_TYPES and msg["msg"]["idx"] == "P1":
                enid = "cover." + (devtype + "_" + agt + "_" + msg["msg"]["me"]).lower()
                attrs = dict(hass.states.get(enid).attributes)
                nval = msg["msg"]["val"]
                ntype = msg["msg"]["type"]
                attrs["current_position"] = nval & 0x7F
                # _LOGGER.debug("websocket_cover_attrs: %s",str(attrs))
                nstat = None
                if ntype % 2 == 0:
                    if nval > 0:
                        nstat = "open"
                    else:
                        nstat = "closed"
                else:
                    if nval & 0x80 == 0x80:
                        nstat = "opening"
                    else:
                        nstat = "closing"
                hass.states.set(enid, nstat, attrs)
            elif devtype in EV_SENSOR_TYPES:
                enid = (
                    "sensor."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = hass.states.get(enid).attributes
                hass.states.set(enid, msg["msg"]["v"], attrs)
            elif devtype in GAS_SENSOR_TYPES and msg["msg"]["val"] > 0:
                enid = (
                    "sensor."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = hass.states.get(enid).attributes
                hass.states.set(enid, msg["msg"]["val"], attrs)
            elif devtype in SPOT_TYPES or devtype in LIGHT_SWITCH_TYPES:
                enid = (
                    "light."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = dict(hass.states.get(enid).attributes)
                _LOGGER.debug("websocket_light_msg: %s ", str(msg))
                _LOGGER.debug("websocket_light_attrs: %s", str(attrs))
                value = msg["msg"]["val"]
                idx = msg["msg"]["idx"]
                
                if msg["msg"]["type"] % 2 == 0:
                    hass.states.set(enid, "off", attrs)
                else:
                    if idx in ["HS"]:
                        if value == 0:
                            attrs[ATTR_HS_COLOR] = None
                        else:
                            rgbhexstr = "%x" % value
                            rgbhexstr = rgbhexstr.zfill(8)
                            rgbhex = bytes.fromhex(rgbhexstr)
                            rgba = struct.unpack("BBBB", rgbhex)
                            rgb = rgba[1:]
                            attrs[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb)
                            _LOGGER.info("hs: %s", str(attrs[ATTR_HS_COLOR]))
                    elif idx in ["RGB_O"]:
                        if value == 0:
                            attrs[ATTR_RGB_COLOR] = None
                        else:
                            rgbhexstr = "%x" % value
                            rgbhexstr = rgbhexstr.zfill(8)
                            rgbhex = bytes.fromhex(rgbhexstr)
                            rgba = struct.unpack("BBBB", rgbhex)
                            rgb = rgba[1:]
                            attrs[ATTR_RGB_COLOR] = rgb
                            _LOGGER.info("rgb: %s", str(attrs[ATTR_RGB_COLOR]))
                    elif idx in ["RGBW", "RGB"]:
                        rgbhexstr = "%x" % value
                        rgbhexstr = rgbhexstr.zfill(8)
                        rgbhex = bytes.fromhex(rgbhexstr)
                        rgbhex = struct.unpack("BBBB", rgbhex)
                        # convert from wrgb to rgbw tuple
                        attrs[ATTR_RGBW_COLOR] = rgbhex[1:] + (rgbhex[0],)
                        _LOGGER.info("rgbw: %s", str(attrs[ATTR_RGBW_COLOR]))

                    hass.states.set(enid, "on", attrs)

            elif devtype in LIGHT_DIMMER_TYPES:
                enid = (
                    "light."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + "P1P2"
                        # + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = dict(hass.states.get(enid).attributes)
                state = hass.states.get(enid).state
                _LOGGER.debug("websocket_light_msg: %s ", str(msg))
                _LOGGER.debug("websocket_light_attrs: %s", str(attrs))
                value = msg["msg"]["val"]
                idx = msg["msg"]["idx"]
                if idx in ["P1"]:
                    if msg["msg"]["type"] % 2 == 1:
                        attrs[ATTR_BRIGHTNESS] = value
                        hass.states.set(enid, "on", attrs)
                    else:
                        hass.states.set(enid, "off", attrs)
                elif idx in ["P2"]:
                    ratio = 1 - (value / 255)
                    attrs[ATTR_COLOR_TEMP] = (
                        int((attrs[ATTR_MAX_MIREDS] - attrs[ATTR_MIN_MIREDS]) * ratio)
                        + attrs[ATTR_MIN_MIREDS]
                    )
                    hass.states.set(enid, state, attrs)

            # elif devtype in QUANTUM_TYPES and msg['msg']['idx'] == "P1":
            #    enid = "light."+(devtype + "_" + agt + "_" + msg['msg']['me'] + "_P1").lower()
            #    attrs = hass.states.get(enid).attributes
            #    hass.states.set(enid, msg['msg']['val'], attrs)
            elif devtype in CLIMATE_TYPES:
                enid = "climate." + (
                    devtype + "_" + agt + "_" + msg["msg"]["me"]
                ).lower().replace(":", "_").replace("@", "_")
                _idx = msg["msg"]["idx"]
                attrs = dict(hass.states.get(enid).attributes)
                nstat = hass.states.get(enid).state
                if _idx == "O":
                    if msg["msg"]["type"] % 2 == 1:
                        nstat = attrs["last_mode"]
                        hass.states.set(enid, nstat, attrs)
                    else:
                        nstat = HVAC_MODE_OFF
                        hass.states.set(enid, nstat, attrs)
                if _idx == "P1":
                    if msg["msg"]["type"] % 2 == 1:
                        nstat = HVAC_MODE_HEAT
                        hass.states.set(enid, nstat, attrs)
                    else:
                        nstat = HVAC_MODE_OFF
                        hass.states.set(enid, nstat, attrs)
                if _idx == "P2":
                    if msg["msg"]["type"] % 2 == 1:
                        attrs["Heating"] = "true"
                        hass.states.set(enid, nstat, attrs)
                    else:
                        attrs["Heating"] = "false"
                        hass.states.set(enid, nstat, attrs)
                elif _idx == "MODE":
                    if msg["msg"]["type"] == 206:
                        if nstat != HVAC_MODE_OFF:
                            nstat = LIFESMART_STATE_LIST[msg["msg"]["val"]]
                        attrs["last_mode"] = nstat
                        hass.states.set(enid, nstat, attrs)
                elif _idx == "F":
                    if msg["msg"]["type"] == 206:
                        attrs["fan_mode"] = get_fan_mode(msg["msg"]["val"])
                        hass.states.set(enid, nstat, attrs)
                elif _idx == "tT" or _idx == "P3":
                    if msg["msg"]["type"] == 136:
                        attrs["temperature"] = msg["msg"]["v"]
                        hass.states.set(enid, nstat, attrs)
                elif _idx == "T" or _idx == "P4":
                    if msg["msg"]["type"] == 8 or msg["msg"]["type"] == 9:
                        attrs["current_temperature"] = msg["msg"]["v"]
                        hass.states.set(enid, nstat, attrs)
            elif devtype in LOCK_TYPES:
                if msg["msg"]["idx"] == "BAT":
                    enid = (
                        "sensor."
                        + (
                            devtype
                            + "_"
                            + agt
                            + "_"
                            + msg["msg"]["me"]
                            + "_"
                            + msg["msg"]["idx"]
                        ).lower()
                    )
                    attrs = hass.states.get(enid).attributes
                    hass.states.set(enid, msg["msg"]["val"], attrs)
                elif msg["msg"]["idx"] == "EVTLO":
                    enid = (
                        "binary_sensor."
                        + (
                            devtype
                            + "_"
                            + agt
                            + "_"
                            + msg["msg"]["me"]
                            + "_"
                            + msg["msg"]["idx"]
                        ).lower()
                    )
                    val = msg["msg"]["val"]
                    ulk_way = val >> 12
                    ulk_user = val & 0xFFF
                    ulk_success = True
                    if ulk_user == 0:
                        ulk_success = False
                    attrs = {
                        "unlocking_way": ulk_way,
                        "unlocking_user": ulk_user,
                        "devtype": devtype,
                        "unlocking_success": ulk_success,
                        "last_time": datetime.datetime.fromtimestamp(
                            msg["msg"]["ts"] / 1000
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    if msg["msg"]["type"] % 2 == 1:
                        hass.states.set(enid, "on", attrs)
                    else:
                        hass.states.set(enid, "off", attrs)
            if devtype in OT_SENSOR_TYPES and msg["msg"]["idx"] in [
                "Z",
                "V",
                "P3",
                "P4",
            ]:
                enid = (
                    "sensor."
                    + (
                        devtype
                        + "_"
                        + agt
                        + "_"
                        + msg["msg"]["me"]
                        + "_"
                        + msg["msg"]["idx"]
                    ).lower()
                )
                attrs = hass.states.get(enid).attributes
                hass.states.set(enid, msg["msg"]["v"], attrs)
            
        # AI event
        if (msg["msg"]["idx"] == "s"
            and msg["msg"]["me"] in ai_include_items
            and msg["msg"]["agt"] in ai_include_agts
            ):
            _LOGGER.info("AI Event: %s",str(msg))
            devtype = msg["msg"]["devtype"]
            agt = msg["msg"]["agt"][:-3]
            enid = (
               "switch."
               + (
                  devtype
                  + "_"
                  + agt
                  + "_"
                  + msg["msg"]["me"]
                  + "_"
                  + msg["msg"]["idx"]
                ).lower()
            )
            attrs = hass.states.get(enid).attributes
           
            if msg["msg"]["stat"] == 3:                    
                hass.states.set(enid, "on", attrs)
            elif msg["msg"]["stat"] == 4:
                hass.states.set(enid, "off", attrs)

    def on_message(ws, message):
        # _LOGGER.info("websocket_msg: %s",str(message))
        msg = json.loads(message)
        if "type" not in msg:
            return
        if msg["type"] != "io":
            return
        asyncio.run(set_Event(msg))

    def on_error(ws, error):
        _LOGGER.error("websocket_error: %s", str(error))

    def on_close(ws, close_status_code, close_msg):
        _LOGGER.debug(
            "lifesmart websocket closed...: %s %s",
            str(close_status_code),
            str(close_msg),
        )

    def on_open(ws):
        tick = int(time.time())
        sdata = (
            "method:WbAuth,time:"
            + str(tick)
            + ",userid:"
            + param["userid"]
            + ",usertoken:"
            + param["usertoken"]
            + ",appkey:"
            + param["appkey"]
            + ",apptoken:"
            + param["apptoken"]
        )
        sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()
        send_values = {
            "id": 1,
            "method": "WbAuth",
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": param["userid"],
                "appkey": param["appkey"],
                "time": tick,
                "sign": sign,
            },
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        ws.send(send_data)
        _LOGGER.debug("lifesmart websocket sending_data...")

    hass.services.async_register(DOMAIN, "send_keys", send_keys)
    hass.services.async_register(DOMAIN, "send_ackeys", send_ackeys)
    hass.services.async_register(DOMAIN, "scene_set", scene_set)

    ws = websocket.WebSocketApp(
        "wss://api.us.ilifesmart.com:8443/wsapp/",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.on_open = on_open
    hass.data[LifeSmart_STATE_MANAGER] = LifeSmartStatesManager(ws=ws)
    hass.data[LifeSmart_STATE_MANAGER].start_keep_alive()
    return True


class LifeSmartDevice(Entity):
    """LifeSmart base device."""

    def __init__(self, dev, idx, val, param):
        """Initialize the switch."""
        if dev["devtype"] in SWTICH_TYPES and dev["devtype"] not in [
            "SL_NATURE",
            "SL_SW_ND1",
            "SL_SW_ND2",
            "SL_SW_ND3",
        ]:
            self._name = dev["name"] + "_" + dev["data"][idx]["name"]
        elif dev["devtype"] in AI_TYPES or dev["devtype"] in LIGHT_DIMMER_TYPES or dev["devtype"] in LIGHT_SWITCH_TYPES:
            self._name = dev["name"]
        else:
            self._name = dev["name"] + "_" + idx
        self._appkey = param["appkey"]
        self._apptoken = param["apptoken"]
        self._usertoken = param["usertoken"]
        self._userid = param["userid"]
        self._agt = dev["agt"]
        self._me = dev["me"]
        self._idx = idx
        self._devtype = dev["devtype"]
        attrs = {
            "agt": self._agt,
            "me": self._me,
            "idx": self._idx,
            "devtype": self._devtype,
        }
        self._attributes = attrs

    @property
    def object_id(self):
        """Return LifeSmart device id."""
        return self.entity_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def name(self):
        """Return LifeSmart device name."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return False

    @property
    def should_poll(self):
        """check with the entity for an updated state."""
        return False

    # @staticmethod
    # def _lifesmart_epset(self, type, val, idx):
    #     # self._tick = int(time.time())
    #     url = "https://api.us.ilifesmart.com/app/api.EpSet"
    #     tick = int(time.time())
    #     appkey = self._appkey
    #     apptoken = self._apptoken
    #     userid = self._userid
    #     usertoken = self._usertoken
    #     agt = self._agt
    #     me = self._me
    #     sdata = (
    #         "method:EpSet,agt:"
    #         + agt
    #         + ",idx:"
    #         + idx
    #         + ",me:"
    #         + me
    #         + ",type:"
    #         + type
    #         + ",val:"
    #         + str(val)
    #         + ",time:"
    #         + str(tick)
    #         + ",userid:"
    #         + userid
    #         + ",usertoken:"
    #         + usertoken
    #         + ",appkey:"
    #         + appkey
    #         + ",apptoken:"
    #         + apptoken
    #     )
    #     sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()
    #     send_values = {
    #         "id": 1,
    #         "method": "EpSet",
    #         "system": {
    #             "ver": "1.0",
    #             "lang": "en",
    #             "userid": userid,
    #             "appkey": appkey,
    #             "time": tick,
    #             "sign": sign,
    #         },
    #         "params": {"agt": agt, "me": me, "idx": idx, "type": type, "val": val},
    #     }
    #     header = {"Content-Type": "application/json"}
    #     send_data = json.dumps(send_values)
    #     req = urllib.request.Request(
    #         url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    #     )
    #     response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    #     # response = json.loads(await asyncPOST(url, send_data, header))
    #     _LOGGER.info("epset_send: %s", str(send_data))
    #     _LOGGER.info("epset_res: %s", str(response))
    #     return response["code"]

    # @staticmethod
    # def _lifesmart_epget(self):
    #     url = "https://api.us.ilifesmart.com/app/api.EpGet"
    #     tick = int(time.time())
    #     appkey = self._appkey
    #     apptoken = self._apptoken
    #     userid = self._userid
    #     usertoken = self._usertoken
    #     agt = self._agt
    #     me = self._me
    #     sdata = (
    #         "method:EpGet,agt:"
    #         + agt
    #         + ",me:"
    #         + me
    #         + ",time:"
    #         + str(tick)
    #         + ",userid:"
    #         + userid
    #         + ",usertoken:"
    #         + usertoken
    #         + ",appkey:"
    #         + appkey
    #         + ",apptoken:"
    #         + apptoken
    #     )
    #     sign = hashlib.md5(sdata.encode(encoding="UTF-8")).hexdigest()
    #     send_values = {
    #         "id": 1,
    #         "method": "EpGet",
    #         "system": {
    #             "ver": "1.0",
    #             "lang": "en",
    #             "userid": userid,
    #             "appkey": appkey,
    #             "time": tick,
    #             "sign": sign,
    #         },
    #         "params": {"agt": agt, "me": me},
    #     }
    #     header = {"Content-Type": "application/json"}
    #     send_data = json.dumps(send_values)
    #     req = urllib.request.Request(
    #         url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
    #     )
    #     response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    #     # response = json.loads(await asyncPOST(url, send_data, header))
    #     return response["message"]["data"]

    @staticmethod
    async def async_lifesmart_epset(self, type, val, idx):
        # self._tick = int(time.time())
        url = "https://api.us.ilifesmart.com/app/api.EpSet"
        tick = int(time.time())
        appkey = self._appkey
        apptoken = self._apptoken
        userid = self._userid
        usertoken = self._usertoken
        agt = self._agt
        me = self._me
        sdata = (
            "method:EpSet,agt:"
            + agt
            + ",idx:"
            + idx
            + ",me:"
            + me
            + ",type:"
            + type
            + ",val:"
            + str(val)
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
            "method": "EpSet",
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": userid,
                "appkey": appkey,
                "time": tick,
                "sign": sign,
            },
            "params": {"agt": agt, "me": me, "idx": idx, "type": type, "val": val},
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        # req = urllib.request.Request(
        #     url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
        # )
        # response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        response = json.loads(await asyncPOST(url, send_data, header))
        # _LOGGER.info("epset_send: %s", str(send_data))
        # _LOGGER.info("epset_res: %s", str(response))
        return response["code"]

    @staticmethod
    async def async_lifesmart_epget(self):
        url = "https://api.us.ilifesmart.com/app/api.EpGet"
        tick = int(time.time())
        appkey = self._appkey
        apptoken = self._apptoken
        userid = self._userid
        usertoken = self._usertoken
        agt = self._agt
        me = self._me
        sdata = (
            "method:EpGet,agt:"
            + agt
            + ",me:"
            + me
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
            "method": "EpGet",
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": userid,
                "appkey": appkey,
                "time": tick,
                "sign": sign,
            },
            "params": {"agt": agt, "me": me},
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        # req = urllib.request.Request(
        #   url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
        # )
        # response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        response = json.loads(await asyncPOST(url, send_data, header))
        return response["message"]["data"]

    @staticmethod
    async def async_lifesmart_sceneset(self, type, rgbw):
        # self._tick = int(time.time())
        url = "https://api.us.ilifesmart.com/app/api.SceneSet"
        tick = int(time.time())
        appkey = self._appkey
        apptoken = self._apptoken
        userid = self._userid
        usertoken = self._usertoken
        agt = self._agt
        id = self._me
        sdata = (
            "method:SceneSet,agt:"
            + agt
            + ",id:"
            + id
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
            "method": "SceneSet",
            "system": {
                "ver": "1.0",
                "lang": "en",
                "userid": userid,
                "appkey": appkey,
                "time": tick,
                "sign": sign,
            },
            "params": {"agt": agt, "id": id},
        }
        header = {"Content-Type": "application/json"}
        send_data = json.dumps(send_values)
        # req = urllib.request.Request(
        #     url=url, data=send_data.encode("utf-8"), headers=header, method="POST"
        # )
        # response = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        response = json.loads(await asyncPOST(url, send_data, header))
        # _LOGGER.info("sceneset_send: %s", str(send_data))
        # _LOGGER.info("sceneset_res: %s", str(response))
        return response["code"]


class LifeSmartStatesManager(threading.Thread):
    def __init__(self, ws):
        """Init LifeSmart Update Manager."""
        threading.Thread.__init__(self)
        self._run = False
        self._lock = threading.Lock()
        self._ws = ws

    def run(self):
        while self._run:
            _LOGGER.debug("lifesmart: starting wss...")
            self._ws.run_forever()
            _LOGGER.debug("lifesmart: restart wss...")
            time.sleep(10)

    def start_keep_alive(self):
        """Start keep alive mechanism."""
        with self._lock:
            self._run = True
            threading.Thread.start(self)

    def stop_keep_alive(self):
        """Stop keep alive mechanism."""
        with self._lock:
            self._run = False
            self.join()
