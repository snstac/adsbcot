#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Functions."""

import datetime

import pycot

import adsbcot.constants

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def adsb_to_cot(craft: dict, cot_type: str = None, # NOQA pylint: disable=too-many-locals
                stale: int = None) -> pycot.Event:
    """
    Transforms a Dump1090 ADS-B Aircraft Object to a Cursor-on-Target PLI.
    """
    time = datetime.datetime.now(datetime.timezone.utc)
    cot_type = cot_type or adsbcot.constants.DEFAULT_TYPE
    stale = stale or adsbcot.constants.DEFAULT_STALE

    lat = craft.get('lat')
    lon = craft.get('lon')

    if lat is None or lon is None:
        return None

    c_hex = craft.get('hex')
    name = f"ICAO24.{c_hex}"
    flight = craft.get('flight', '').strip()
    if flight:
        callsign = flight
    else:
        callsign = c_hex

    point = pycot.Point()
    point.lat = lat
    point.lon = lon
    point.ce = '10'
    point.le = '10'

    point.hae = craft.get('alt_geom', craft.get('alt_baro', 0))

    uid = pycot.UID()
    uid.Droid = name

    contact = pycot.Contact()
    contact.callsign = callsign
    # Not supported by FTS 1.1?
    # if flight:
    #    contact.hostname = f'https://flightaware.com/live/flight/{flight}'

    track = pycot.Track()
    track.course = craft.get('track', 0)
    track.speed = craft.get('gs', 0)

    remarks = pycot.Remarks()
    _remark = (f"ICAO24: {c_hex} Squawk: {craft.get('squawk')} "
               f"RSSI: {craft.get('rssi')}")
    if flight:
        remarks.value = f"Flight: {flight} " + _remark
    else:
        remarks.value = _remark

    detail = pycot.Detail()
    detail.uid = uid
    detail.contact = contact
    detail.track = track
    # Not supported by FTS 1.1?
    # detail.remarks = remarks

    event = pycot.Event()
    event.version = '2.0'
    event.event_type = cot_type
    event.uid = name
    event.time = time
    event.start = time
    event.stale = time + datetime.timedelta(hours=stale)
    event.how = 'm-g'
    event.point = point
    event.detail = detail

    return event
