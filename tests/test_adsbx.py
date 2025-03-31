#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""adsbcot Module Tests."""

import csv
import io

import xml.etree.ElementTree as ET

import pytest
import adsbcot.functions

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


@pytest.fixture
def sample_feed():
    return {
        "aircraft": [
            {
                "alt_baro": 3700,
                "alt_geom": 3750,
                "category": "A1",
                "flight": "N739UL  ",
                "geom_rate": 512,
                "gs": 79.5,
                "gva": 2,
                "hex": "a9ee47",
                "lat": 37.836449,
                "lon": -122.030281,
                "messages": 34,
                "mlat": [],
                "nac_p": 10,
                "nac_v": 2,
                "nic": 9,
                "nic_baro": 0,
                "rc": 75,
                "rssi": -15.8,
                "sda": 2,
                "seen": 0.2,
                "seen_pos": 1.0,
                "sil": 3,
                "sil_type": "perhour",
                "tisb": [],
                "track": 50.1,
                "version": 2,
            },
            {
                "alt_baro": 37000,
                "alt_geom": 38650,
                "baro_rate": 0,
                "gs": 487.6,
                "hex": "3c4586",
                "messages": 10,
                "mlat": [],
                "nac_v": 1,
                "rssi": -18.2,
                "seen": 17.0,
                "tisb": [],
                "track": 171.3,
                "version": 0,
            },
            {
                "alt_baro": 39000,
                "hex": "a18b41",
                "lat": 39.455023,
                "lon": -120.402344,
                "messages": 17,
                "mlat": [],
                "nac_p": 10,
                "nav_altitude_mcp": 39008,
                "nav_modes": ["autopilot", "vnav", "tcas"],
                "nav_qnh": 1013.6,
                "nic": 8,
                "nic_baro": 1,
                "rc": 186,
                "rssi": -18.9,
                "seen": 3.2,
                "seen_pos": 12.6,
                "sil": 3,
                "sil_type": "unknown",
                "squawk": "3514",
                "tisb": [],
                "version": 0,
            },
            {
                "alt_baro": 17650,
                "alt_geom": 18650,
                "baro_rate": -2112,
                "category": "A3",
                "flight": "SWA1241 ",
                "gs": 353.4,
                "hex": "abd994",
                "messages": 14,
                "mlat": [],
                "nac_p": 8,
                "nac_v": 1,
                "nav_altitude_mcp": 3392,
                "nav_heading": 308.0,
                "nav_qnh": 1013.6,
                "nic_baro": 1,
                "rssi": -18.1,
                "seen": 16.7,
                "sil": 2,
                "sil_type": "unknown",
                "tisb": [],
                "track": 321.1,
                "version": 0,
            },
        ],
        "messages": 1799595081,
        "now": 1602849987.1,
    }


@pytest.fixture
def sample_known_craft():
    sample_csv = """DOMAIN,AGENCY,REG,CALLSIGN,TYPE,MODEL,HEX,COT,TYPE,,
EMS,CALSTAR,N832CS,CALSTAR7,HELICOPTER,,,a-f-A-C-H,HELICOPTER,,
EMS,REACH AIR MEDICAL,N313RX,REACH16,HELICOPTER,,,a-f-A-C-H,HELICOPTER,,
FED,USCG,1339,C1339,FIXED WING,,,,FIXED WING,,
FIRE,USFS,N143Z,JUMPR43,FIXED WING,DH6,,a-f-A-C-F,FIXED WING,,
FIRE,,N17085,TNKR_911,FIXED WING,,,a-f-A-C-F,FIXED WING,,
FIRE,CAL FIRE,N481DF,C_104,HELICOPTER,,,a-f-A-C-H,HELICOPTER,,
FOOD,EL FAROLITO,N739UL,TACO_01,HELICOPTER,,,a-f-A-T-A-C-O,HELICOPTER,,
FOOD,PANCHO VIA,N708SD,TACO_03,HELICOPTER,,,a-f-A-T-A-C-O,HELICOPTER,,
"""
    csv_fd = io.StringIO(sample_csv)
    all_rows = []
    reader = csv.DictReader(csv_fd)
    for row in reader:
        all_rows.append(row)
    return all_rows


def test_adsb_to_cot_xml(sample_feed):
    """Tests that ADS-B to COT translation returns expected XML Document."""
    sample_craft = sample_feed["aircraft"][0]
    cot = adsbcot.functions.adsb_to_cot_xml(sample_craft)
    print(ET.tostring(cot))

    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-n-A-C-F"
    assert cot.attrib["uid"] == "ICAO-A9EE47"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.836449"
    assert point[0].attrib["lon"] == "-122.030281"
    assert point[0].attrib["hae"] == "1143.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].attrib["callsign"] == "N739UL"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "50.1"
    assert track[0].attrib["speed"] == "40.898298000000004"

    __adsb = detail[0].findall("__adsb")
    assert __adsb[0].attrib["flight"] == "N739UL"
    assert __adsb[0].attrib["icao"] == "A9EE47"
    assert __adsb[0].attrib["cat"] == "A1"


def test_adsb_to_cot(sample_feed):
    """Tests that ADS-B to COT translation returns expected XML as a sring."""
    sample_craft = sample_feed["aircraft"][0]
    cot = adsbcot.adsb_to_cot(sample_craft)
    expected = (
        b'<event version="2.0" type="a-.-A-C-F" uid="ICAO-A9EE47" how="m-g" '
        b'time="2021-05-19T22:07:38.928623Z" start="2021-05-19T22:07:38.928623Z" '
        b'stale="2021-05-19T22:09:38.928623Z"><point lat="37.836449" lon="-122.030281" ce="10" le="2" '
        b'hae="1143.0" /><detail uid="ICAO-A9EE47" remarks="N739UL-- ICAO: A9EE47 REG:  Flight: N739UL Type:  '
        b'Squawk: None Category: A1 (via adsbcot@rorqual)"><UID Droid="ICAO-A9EE47" />'
        b'<contact callsign="N739UL--" /><track course="50.1" speed="40.641076" /><remarks>N739UL-- ICAO: '
        b"A9EE47 REG:  Flight: N739UL Type:  Squawk: None Category: A1 (via adsbcot@rorqual)</remarks>"
        b"</detail></event>"
    )
    assert isinstance(cot, bytes)
    assert b"a-n-A-C-F" in cot
    assert b"N739UL" in cot
    assert b"ICAO-A9EE47" in cot
    assert b'speed="40.898298000000004"' in cot


def test_adsb_to_cot_with_known_craft(sample_feed, sample_known_craft):
    sample_craft = sample_feed["aircraft"][0]
    known_craft_key = "REG"
    filter_key = sample_craft["flight"].strip().upper()

    known_craft = (
        list(
            filter(
                lambda x: x[known_craft_key].strip().upper() == filter_key,
                sample_known_craft,
            )
        )
        or [{}]
    )[0]

    cot = adsbcot.functions.adsb_to_cot_xml(sample_craft, known_craft=known_craft)
    print(ET.tostring(cot))

    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-f-A-T-A-C-O"
    assert cot.attrib["uid"] == "ICAO-A9EE47"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.836449"
    assert point[0].attrib["lon"] == "-122.030281"
    assert point[0].attrib["hae"] == "1143.0"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    contact = detail[0].findall("contact")
    assert contact[0].attrib["callsign"] == "TACO_01"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "50.1"
    assert track[0].attrib["speed"] == "40.898298000000004"

    __adsb = detail[0].findall("__adsb")
    assert __adsb[0].attrib["flight"] == "N739UL"
    assert __adsb[0].attrib["icao"] == "A9EE47"
    assert __adsb[0].attrib["cat"] == "A1"


def test_negative_adsbx_to_cot():
    """
    Tests that `adsbx_to_cot()` returns None for an invalid craft.
    """
    sample_craft = {"taco": "burrito"}
    cot = adsbcot.adsb_to_cot(sample_craft)
    assert cot == None
