#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""ADSBCOT Functions."""

import asyncio
import importlib.util
import logging
import os
import warnings
import xml.etree.ElementTree as ET

from configparser import SectionProxy
from typing import Optional, Set, Union
from urllib.parse import ParseResult, urlparse

import aircot
import pytak
import adsbcot

# We won't use pyModeS if it isn't installed:
try:
    import pyModeS  # NOQA pylint: disable=unused-import
except ImportError as exc:
    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError for: pyModeS")


APP_NAME = "adsbcot"
Logger = logging.getLogger(__name__)
Debug = bool(os.getenv("DEBUG", False))


def create_tasks(config: SectionProxy, clitool: pytak.CLITool) -> Set[pytak.Worker,]:
    """Create specific coroutine task set for this application.

    Parameters
    ----------
    config : `SectionProxy`
        Configuration options & values.
    clitool : `pytak.CLITool`
        A PyTAK Worker class instance.

    Returns
    -------
    `set`
        Set of PyTAK Worker classes for this application.
    """
    tasks = set()

    _feed_url: str = config.get("FEED_URL", adsbcot.DEFAULT_FEED_URL)
    config.setdefault("FEED_URL", _feed_url)
    _feed_url = config.get("FEED_URL", "")

    if "://" not in _feed_url:
        warnings.warn(f"Invalid FEED_URL: '{_feed_url}'", SyntaxWarning)
        raise ValueError(
            "Please specify FEED_URL with full URL, including '://', for "
            "example: tcp+beast://example.com:30005"
        )

    # Gateway code:
    feed_url: ParseResult = urlparse(config.get("FEED_URL", ""))

    # ADS-B Workers (receivers):
    if feed_url.scheme in ["http", "file", "ws", "wss"]:
        # HTTP, WebSocket, or file-based input:
        tasks.add(adsbcot.ADSBWorker(clitool.tx_queue, config))
    elif "tcp" in feed_url.scheme:
        if importlib.util.find_spec("pyModeS") is None:
            warnings.warn(
                (
                    f"Please reinstall {APP_NAME} with pyModeS support:"
                    f"$ python3 -m pip install {APP_NAME}[with_pymodes]"
                ),
                ImportWarning,
            )
            raise ValueError

        net_queue: asyncio.Queue = asyncio.Queue()

        if "+" in feed_url.scheme:
            _, data_type = feed_url.scheme.split("+")
        else:
            data_type = "raw"

        tasks.add(adsbcot.ADSBNetReceiver(net_queue, config, data_type))

        tasks.add(adsbcot.ADSBNetWorker(clitool.tx_queue, net_queue, config, data_type))

    return tasks


def adsb_to_cot_xml(  # NOQA pylint: disable=too-many-locals,too-many-branches,too-many-statements
    craft: dict,
    config: Union[SectionProxy, dict, None] = None,
    known_craft: Optional[dict] = None,
) -> Optional[ET.Element]:
    """
    Serialize ADS-B data as Cursor on Target.

    Parameters
    ----------
    craft : `dict`
        Key/Value data struct of decoded ADS-B aircraft data.
    config : `configparser.SectionProxy`
        Configuration options and values.
        Uses config options: UID_KEY, COT_STALE, COT_HOST_ID
    kown_craft : `dict`
        Optional list of know craft to transform CoT data.

    Returns
    -------
    `xml.etree.ElementTree.Element`
        Cursor-On-Target XML ElementTree object.
    """
    lastPosition = craft.get("lastPosition")
    if lastPosition:
        craft.update(lastPosition)

    lat = craft.get("lat", craft.get("Lat"))
    lon = craft.get("lon", craft.get("Lon", craft.get("Lng")))

    if lat is None or lon is None:
        Logger.warning(f"No value for lat={lat} lon={lon}")
        return None

    remarks_fields = []
    known_craft = known_craft or {}
    config = config or {}
    category = None
    tisb: bool = False

    uid_key: str = config.get("UID_KEY", "ICAO")
    cot_stale: int = int(config.get("COT_STALE", pytak.DEFAULT_COT_STALE))
    cot_host_id: str = config.get("COT_HOST_ID", pytak.DEFAULT_HOST_ID)

    __adsb = ET.Element("__adsb")
    __adsb.set("cot_host_id", cot_host_id)

    # Stratux reports Icao_addr as an int:
    icao_addr: str = aircot.icao_int_to_hex(
        craft.get("icao_addr", craft.get("Icao_addr", 0))
    )
    icao_hex: str = str(craft.get("hex", craft.get("icao", icao_addr))).strip().upper()

    _flight = craft.get("flight", craft.get("Tail", ""))
    flight: str = str(_flight).strip().upper()

    _reg = craft.get("reg", craft.get("r", craft.get("Reg", "")))
    reg: str = str(_reg).strip().upper()

    _cat = craft.get("cat", craft.get("Category", craft.get("category", "")))
    cat: str = str(_cat).strip().upper()

    _squawk = craft.get("squawk", craft.get("Squawk", ""))
    squawk: str = str(_squawk).strip().upper()

    _type = craft.get("t", craft.get("TargetType", 0))
    craft_type: str = str(_type).strip().upper()

    alt_upper: int = int(config.get("ALT_UPPER", "0"))
    alt_lower: int = int(config.get("ALT_LOWER", "0"))

    alt_geom = craft.get("alt_geom")

    if alt_geom:
        remarks_fields.append(f"Alt:{craft.get('alt_geom')}")
        if alt_upper and alt_upper != 0:
            if alt_geom > alt_upper:
                Logger.warning(
                    f"alt_upper={alt_upper} alt_geom={alt_geom} "
                    "altitude too high, ignoring COT"
                )
                return None
        if alt_lower and alt_lower != 0:
            if alt_geom < alt_lower:
                Logger.warning(
                    f"alt_lower={alt_lower} alt_geom={alt_geom} "
                    "altitude too low, ignoring COT"
                )
                return None
    __adsb.set("alt_geom", str(craft.get("alt_geom")))
    __adsb.set("x_alt_geom", str(craft.get("x_alt_geom")))
    __adsb.set("alt_baro", str(craft.get("alt_baro")))
    __adsb.set("x_alt_baro_offset", str(craft.get("x_alt_baro_offset")))

    if flight:
        remarks_fields.append(flight)
        __adsb.set("flight", flight)

    if reg:
        remarks_fields.append(reg)
        __adsb.set("reg", reg)

    if squawk:
        remarks_fields.append(f"Squawk: {squawk}")
        __adsb.set("squawk", squawk)

    if icao_hex:
        remarks_fields.append(icao_hex)
        __adsb.set("icao", icao_hex)

    if cat:
        category = aircot.set_category(cat, known_craft)
        remarks_fields.append(f"Cat.: {cat}")
        __adsb.set("cat", cat)

    if craft_type:
        __adsb.set("craft_type", str(craft_type))
        remarks_fields.append(f"Type:{craft_type}")

        craft_type_name: Union[str, None] = None
        if craft_type == 0:
            craft_type_name = "Mode S"
        elif craft_type == 1:
            craft_type_name = "ADS-B"
        elif craft_type == 2:
            craft_type_name = "ADS-R"
        elif craft_type == 3:
            craft_type_name = "TIS-B S"
            tisb = True
        elif craft_type == 4:
            craft_type_name = "TIS-B"
            tisb = True
        if craft_type_name:
            remarks_fields.append(f"ADS-B Type: {craft_type}")
            __adsb.set("craft_type", craft_type)

    cot_uid: str = ""
    if "REG" in uid_key and reg:
        cot_uid = f"REG-{reg}"
    elif "ICAO" in uid_key and icao_hex:
        cot_uid = f"ICAO-{icao_hex}"
    if "FLIGHT" in uid_key and flight:
        cot_uid = f"FLIGHT-{flight}"
    elif icao_hex:
        cot_uid = f"ICAO-{icao_hex}"
    elif flight:
        cot_uid = f"FLIGHT-{flight}"
    else:
        Logger.warning(f"cot_uid={cot_uid}")
        return None

    if flight:
        callsign = flight
    elif reg:
        callsign = reg
    else:
        callsign = icao_hex

    _, callsign = aircot.set_name_callsign(
        icao_hex, reg, craft_type, flight, known_craft
    )

    cat = aircot.set_category(cat, known_craft)

    if tisb:
        cot_type = "a-u-A"
    else:
        cot_type = aircot.set_cot_type(icao_hex, category, flight, known_craft)

    nac_p = craft.get("NACp", craft.get("nac_p", 0.0))
    nac_v = craft.get("NACv", craft.get("nac_v", nac_p))

    if craft.get("OnGround"):
        ground_const = 51.56
        hae = pytak.DEFAULT_COT_VAL
    else:
        ground_const = 56.57
        # Multiply alt_geom by "Clarke 1880 (international foot)"
        hae = aircot.functions.get_hae(
            craft.get("Alt", craft.get("alt_geom", craft.get("alt_geom_x")))
        )

    ce = str(float(nac_p) + ground_const)
    le = str(float(nac_v) + 12.5)

    contact: ET.Element = ET.Element("contact")
    contact.set("callsign", callsign)

    uid = ET.Element("UID")
    uid.set("Droid", str(callsign))

    track: ET.Element = ET.Element("track")

    course = craft.get(
        "trk", craft.get("track", craft.get("Track", pytak.DEFAULT_COT_VAL))
    )
    track.set("course", str(course))

    _speed = craft.get("gs", craft.get("Speed", 0.0))
    speed = aircot.functions.get_speed(_speed)
    track.set("speed", str(speed))

    track.set("slope", str(craft.get("Vvel", pytak.DEFAULT_COT_VAL)))

    _radio = ET.Element("_radio")
    _signal = craft.get("SignalLevel", craft.get("rssi"))
    if _signal:
        __adsb.set("signalLevel", str(_signal))
        _radio.set("signal", str(_signal))

    remarks_fields.append(f"FEED_URL: {config.get('FEED_URL', '')}")
    __adsb.set("feed_url", config.get("FEED_URL", ""))
    # Remarks should always be the first sub-entity within the Detail entity.
    remarks = ET.Element("remarks")
    remarks_fields.append(f"{cot_host_id}")
    _remarks = " ".join(list(filter(None, remarks_fields)))
    remarks.text = _remarks

    detail = ET.Element("detail")
    detail.append(track)
    detail.append(contact)
    detail.append(remarks)
    detail.append(__adsb)
    detail.append(_radio)

    icon = known_craft.get("ICON")
    if icon:
        usericon = ET.Element("usericon")
        usericon.set("iconsetpath", icon)
        detail.append(usericon)

    cot_d = {
        "lat": str(lat),
        "lon": str(lon),
        "ce": str(ce),
        "le": str(le),
        "hae": str(hae),
        "uid": cot_uid,
        "cot_type": cot_type,
        "stale": cot_stale,
    }
    cot = pytak.gen_cot_xml(**cot_d)
    cot.set("access", config.get("COT_ACCESS", pytak.DEFAULT_COT_ACCESS))
    cot.set("qos", "1-r-c")

    _detail = cot.findall("detail")[0]
    flowtags = _detail.findall("_flow-tags_")
    detail.extend(flowtags)
    cot.remove(_detail)
    cot.append(detail)

    return cot


def adsb_to_cot(
    craft: dict,
    config: Union[SectionProxy, dict, None] = None,
    known_craft: Optional[dict] = None,
) -> Optional[bytes]:
    """Return CoT XML object as an XML string."""
    cot: Optional[ET.Element] = adsb_to_cot_xml(craft, config, known_craft)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot else None
    )
