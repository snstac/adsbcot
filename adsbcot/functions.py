#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Functions."""

import datetime
import os
import platform

import xml.etree.ElementTree as ET

import aircot
import pytak

import adsbcot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


def adsb_to_cot_xml(  # pylint: disable=too-many-locals,too-many-statements
    craft: dict, cot_type: str = None, stale: int = None
) -> ET.Element:
    """
    Transforms a Dump1090 ADS-B Aircraft Object to a Cursor-on-Target PLI XML.
    """
    time = datetime.datetime.now(datetime.timezone.utc)
    cot_stale = stale or adsbcot.DEFAULT_COT_STALE

    lat = craft.get("lat")
    lon = craft.get("lon")

    if lat is None or lon is None:
        return None

    icao_hex = craft.get("hex", "").upper()
    if not icao_hex:
        return None

    name = f"ICAO-{icao_hex}"

    flight = craft.get("flight", "").strip()
    if flight:
        callsign = flight
    else:
        callsign = icao_hex

    cot_type = aircot.adsb_to_cot_type(craft.get("hex"), craft.get("category"), flight)

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
    uid.set("Droid", name)

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
    detail.set("uid", name)
    detail.append(uid)
    detail.append(contact)
    detail.append(track)

    remarks = ET.Element("remarks")
    _remarks = f"Squawk: {craft.get('squawk')} Category: {craft.get('category')}"

    if flight:
        _remarks = f"{icao_hex}({flight}) {_remarks}"
    else:
        _remarks = f"{icao_hex} {_remarks}"

    if bool(os.environ.get("DEBUG")):
        _remarks = f"{_remarks} via (via adsbxcot@{platform.node()})"

    detail.set("remarks", _remarks)
    remarks.text = _remarks
    detail.append(remarks)

    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", cot_type)
    root.set("uid", name)
    root.set("how", "m-g")
    root.set("time", time.strftime(pytak.ISO_8601_UTC))
    root.set("start", time.strftime(pytak.ISO_8601_UTC))
    root.set(
        "stale",
        (time + datetime.timedelta(seconds=int(cot_stale))).strftime(
            pytak.ISO_8601_UTC
        ),
    )
    root.append(point)
    root.append(detail)

    return root


def adsb_to_cot(craft: dict, cot_type: str = None, stale: int = None) -> bytes:
    """
    Transforms a Dump1090 ADS-B Aircraft Object to a Cursor-on-Target PLI String.
    """
    return ET.tostring(adsb_to_cot_xml(craft, cot_type, stale))
