#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
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
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""ADSBCOT Functions."""

import asyncio
import xml.etree.ElementTree as ET

from configparser import SectionProxy
from typing import Union, Set
from urllib.parse import ParseResult, urlparse

import aircot
import pytak
import adsbcot


__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


APP_NAME = "adsbcot"

# We won't use pyModeS if it isn't installed:
WITH_PYMODES = False
try:
    import pyModeS  # NOQA pylint: disable=unused-import

    WITH_PYMODES = True
except ImportError:
    pass


def create_tasks(
    config: SectionProxy, clitool: pytak.CLITool
) -> Set[pytak.Worker,]:
    """
    Creates specific coroutine task set for this application.

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

    _dump1090_url: str = config.get("DUMP1090_URL", adsbcot.DEFAULT_DUMP1090_URL)
    config.setdefault("DUMP1090_URL", _dump1090_url)

    if "://" not in config.get("DUMP1090_URL"):
        raise Exception(
            "Please specify DUMP1090_URL with full URL, including '://', for "
            "example: tcp+beast://example.com:30005"
        )

    # Gateway code:
    dump1090_url: ParseResult = urlparse(config.get("DUMP1090_URL"))

    # ADS-B Workers (receivers):
    if "http" in dump1090_url.scheme:
        tasks.add(adsbcot.ADSBWorker(clitool.tx_queue, config))
    elif "tcp" in dump1090_url.scheme:
        if not WITH_PYMODES:
            print(f"ERROR from {APP_NAME}")
            print(f"Please reinstall {APP_NAME} with pyModeS support: ")
            print(f"$ python3 -m pip install {APP_NAME}[with_pymodes]")
            print("Exiting...")
            raise Exception

        net_queue: asyncio.Queue = asyncio.Queue()

        if "+" in dump1090_url.scheme:
            _, data_type = dump1090_url.scheme.split("+")
        else:
            data_type = "raw"

        tasks.add(adsbcot.ADSBNetReceiver(net_queue, config, data_type))

        tasks.add(adsbcot.ADSBNetWorker(clitool.tx_queue, net_queue, config, data_type))

    return tasks


def adsb_to_cot_xml(  # NOQA pylint: disable=too-many-locals,too-many-branches,too-many-statements
    craft: dict,
    config: Union[SectionProxy, None] = None,
    known_craft: Union[dict, None] = None,
) -> Union[ET.Element, None]:
    """
    Serializes a Dump1090 ADS-B aircraft object as Cursor-on-Target XML.

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

    known_craft: dict = known_craft or {}
    config: dict = config or {}
    remarks_fields = []

    uid_key = config.get("UID_KEY", "ICAO")
    cot_stale = int(config.get("COT_STALE", pytak.DEFAULT_COT_STALE))
    cot_host_id = config.get("COT_HOST_ID", pytak.DEFAULT_HOST_ID)

    aircotx = ET.Element("_aircot_")
    aircotx.set("cot_host_id", cot_host_id)

    icao_hex = craft.get("hex", "")
    reg = craft.get("reg", "")
    flight = craft.get("flight", "")
    cat = craft.get("category")
    squawk = craft.get("squawk")

    if flight:
        flight = flight.strip().upper()
        remarks_fields.append(flight)
        aircotx.set("flight", flight)

    if reg:
        reg = reg.strip().upper()
        remarks_fields.append(reg)
        aircotx.set("reg", reg)

    if squawk:
        squawk = squawk.strip().upper()
        remarks_fields.append(f"Squawk: {squawk}")
        aircotx.set("squawk", squawk)

    if icao_hex:
        icao_hex = icao_hex.strip().upper()
        remarks_fields.append(icao_hex)
        aircotx.set("icao", icao_hex)

    if cat:
        cat = cat.strip().upper()
        remarks_fields.append(f"Cat.: {cat}")
        aircotx.set("cat", cat)

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

    _, callsign = aircot.set_name_callsign(icao_hex, reg, None, flight, known_craft)
    cat = aircot.set_category(cat, known_craft)
    cot_type = aircot.set_cot_type(icao_hex, cat, flight, known_craft)

    point: ET.Element = ET.Element("point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("ce", str(craft.get("nac_p", "9999999.0")))
    point.set("le", str(craft.get("nac_v", "9999999.0")))

    # alt_geom: geometric (GNSS / INS) altitude in feet referenced to the
    #           WGS84 ellipsoid
    alt_geom = int(craft.get("alt_geom", 0))
    if alt_geom:
        point.set("hae", str(alt_geom * 0.3048))
    else:
        point.set("hae", "9999999.0")

    uid: ET.Element = ET.Element("UID")
    uid.set("Droid", cot_uid)

    contact: ET.Element = ET.Element("contact")
    contact.set("callsign", callsign)

    track: ET.Element = ET.Element("track")
    track.set("course", str(craft.get("trk", "9999999.0")))

    # gs: ground speed in knots
    gnds = int(craft.get("gs", 0))
    if gnds:
        track.set("speed", str(gnds * 0.514444))
    else:
        track.set("speed", "9999999.0")

    detail = ET.Element("detail")
    detail.set("uid", cot_uid)
    detail.append(uid)
    detail.append(contact)
    detail.append(track)

    remarks = ET.Element("remarks")

    remarks_fields.append(f"{cot_host_id}")

    _remarks = " ".join(list(filter(None, remarks_fields)))

    remarks.text = _remarks
    detail.append(remarks)

    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", cot_uid)
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(cot_stale))

    root.append(point)
    root.append(detail)
    root.append(aircotx)

    return root


def adsb_to_cot(
    craft: dict,
    config: Union[SectionProxy, None] = None,
    known_craft: Union[dict, None] = None,
) -> Union[bytes, None]:
    """Wrapper that returns COT as an XML string."""
    cot: Union[ET.Element, None] = adsb_to_cot_xml(craft, config, known_craft)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot else None
    )
