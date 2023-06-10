#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Sensors & Signals LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
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
import warnings
import xml.etree.ElementTree as etree

from configparser import SectionProxy
from typing import Optional, Set, Union
from urllib.parse import ParseResult, urlparse

import aircot
import pytak
import adsbcot

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"


APP_NAME = "adsbcot"

# We won't use pyModeS if it isn't installed:
try:
    import pyModeS  # NOQA pylint: disable=unused-import
except ImportError:
    pass


def create_tasks(
    config: SectionProxy, clitool: pytak.CLITool
) -> Set[pytak.Worker,]:
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
    feed_url: ParseResult = urlparse(config.get("FEED_URL"))

    # ADS-B Workers (receivers):
    if feed_url.scheme in ["http", "file"]:
        tasks.add(adsbcot.ADSBWorker(clitool.tx_queue, config))
    elif "tcp" in feed_url.scheme:
        if importlib.util.find_spec("pyModeS") is None:
            warnings.warn(
                (f"Please reinstall {APP_NAME} with pyModeS support:"
                 f"$ python3 -m pip install {APP_NAME}[with_pymodes]"), 
                 ImportWarning)
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
) -> Optional[etree.Element]:
    """Serialize a Dump1090 ADS-B aircraft object as Cursor on Target XML.

    Parameters
    ----------
    craft : `dict`
        Key/Value data struct of decoded ADS-B aircraft data.
    config : `configparser.SectionProxy`
        Configuration options and values.
        Uses config options: UID_KEY, COT_STALE, COT_HOST_ID

    Returns
    -------
    `xml.etree.ElementTree.Element`
        Cursor-On-Target XML ElementTree object.
    """
    lat = craft.get("lat")
    lon = craft.get("lon")

    if lat is None or lon is None:
        return None

    known_craft = known_craft or {}
    config = config or {}

    remarks_fields: list = []

    uid_key: str = config.get("UID_KEY", "ICAO")
    cot_stale: int = int(config.get("COT_STALE", pytak.DEFAULT_COT_STALE))
    cot_host_id: str = config.get("COT_HOST_ID", pytak.DEFAULT_HOST_ID)

    aircotx = etree.Element("_aircot_")
    aircotx.set("cot_host_id", cot_host_id)

    icao_hex: str = str(craft.get("hex", craft.get("icao", ""))).strip().upper()
    reg: str = str(craft.get("reg", craft.get("r", ""))).strip().upper()
    flight: str = str(craft.get("flight", "")).strip().upper()
    cat: str = str(craft.get("category", "")).strip().upper()
    squawk: str = str(craft.get("squawk", "")).strip().upper()
    craft_type: str = str(craft.get("t", "")).strip().upper()

    if flight:
        remarks_fields.append(flight)
        aircotx.set("flight", flight)

    if reg:
        remarks_fields.append(reg)
        aircotx.set("reg", reg)

    if squawk:
        remarks_fields.append(f"Squawk: {squawk}")
        aircotx.set("squawk", squawk)

    if icao_hex:
        remarks_fields.append(icao_hex)
        aircotx.set("icao", icao_hex)

    if cat:
        remarks_fields.append(f"Cat.: {cat}")
        aircotx.set("cat", cat)

    if craft_type:
        remarks_fields.append(f"Type:{craft_type}")
        aircotx.set("type", craft_type)

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
        return None

    if flight:
        callsign = flight
    elif reg:
        callsign = reg
    else:
        callsign = icao_hex

    _, callsign = aircot.set_name_callsign(icao_hex, reg, craft_type, flight, known_craft)
    cat = aircot.set_category(cat, known_craft)
    cot_type = aircot.set_cot_type(icao_hex, cat, flight, known_craft)

    point: etree.Element = etree.Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("ce", str(craft.get("nac_p", "9999999.0")))
    point.set("le", str(craft.get("nac_v", "9999999.0")))
    point.set("hae", aircot.functions.get_hae(craft.get("alt_geom")))

    contact: etree.Element = etree.Element("contact")
    contact.set("callsign", callsign)

    track: etree.Element = etree.Element("track")
    track.set("course", str(craft.get("trk", craft.get("track", "9999999.0"))))
    track.set("speed", aircot.functions.get_speed(craft.get("gs")))

    detail = etree.Element("detail")
    detail.append(contact)
    detail.append(track)

    icon = known_craft.get("ICON")
    if icon:
        usericon = etree.Element("usericon")
        usericon.set("iconsetpath", icon)
        detail.append(usericon)

    remarks = etree.Element("remarks")

    remarks_fields.append(f"{cot_host_id}")

    _remarks = " ".join(list(filter(None, remarks_fields)))

    remarks.text = _remarks
    detail.append(remarks)
    detail.append(aircotx)

    root = etree.Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", cot_uid)
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(cot_stale))

    root.append(point)
    root.append(detail)

    return root


def adsb_to_cot(
    craft: dict,
    config: Union[SectionProxy, dict, None] = None,
    known_craft: Optional[dict] = None,
) -> Optional[bytes]:
    """Return CoT XML object as an XML string."""
    cot: Optional[etree.Element] = adsb_to_cot_xml(craft, config, known_craft)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, etree.tostring(cot)]) if cot else None
    )
