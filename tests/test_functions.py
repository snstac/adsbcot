#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Function Tests."""

import unittest

import xml.etree.ElementTree as ET

import adsbcot

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


TEST_DUMP1090_FEED = {
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


class FunctionsTestCase(unittest.TestCase):
    """
    Test class for functions... functions.
    """

    def test_adsb_to_cot(self):
        """
        Tests that adsb_to_cot decodes ADS-B into a Cursor-on-Target
        message.
        """
        aircraft = TEST_DUMP1090_FEED["aircraft"]
        craft = aircraft[0]
        cot = adsbcot.functions.adsb_to_cot_xml(craft)

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
        assert detail[0].attrib["uid"] == "ICAO-A9EE47"

        track = detail[0].findall("track")
        assert track[0].attrib["course"] == "9999999.0"
        assert track[0].attrib["speed"] == "40.641076"


if __name__ == "__main__":
    unittest.main()
