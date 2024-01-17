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

"""ADSBCOT Function Tests."""

import unittest
import xml.etree.ElementTree as etree

import adsbcot

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright 2023 Sensors & Signals LLC"
__license__ = "Apache License, Version 2.0"


TEST_FEED = {
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
            "reg": "test_reg_1234",
            "squawk": "3514",
            "t": "test_craft_type_1234",
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

    def test_adsb_to_cot_xml(self):
        """Test that adsb_to_cot serializses ADS-B as valid Cursor on Target XML Object."""
        aircraft = TEST_FEED["aircraft"]
        craft = aircraft[0]
        cot = adsbcot.functions.adsb_to_cot_xml(craft)
        print("COT: %s", cot)
        assert isinstance(cot, etree.Element)
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

        track = detail[0].findall("track")
        assert track[0].attrib["course"] == "50.1"
        assert track[0].attrib["speed"] == "40.898298000000004"

    def test_adsb_to_cot(self):
        """Test that adsb_to_cot serializses ADS-B as valid Cursor on Target XML String."""
        aircraft = TEST_FEED["aircraft"]
        craft = aircraft[0]
        cot = adsbcot.functions.adsb_to_cot(craft)
        assert b"ICAO-A9EE47" in cot
        assert b"a-n-A-C-F" in cot
        assert b"37.836449" in cot
        assert b"-122.030281" in cot
        assert b"1143.0" in cot

    def test_adsb_to_cot_no_lat(self):
        """Test that adsb_to_cot rejects adsb with not valid latitude."""
        aircraft = TEST_FEED["aircraft"]
        craft = aircraft[2]
        del craft["lat"]
        cot = adsbcot.functions.adsb_to_cot_xml(craft)
        assert cot is None

    def test_adsb_to_cot_no_lon(self):
        """Test that adsb_to_cot rejects adsb with not valid longitude."""
        aircraft = TEST_FEED["aircraft"]
        craft = aircraft[2]
        del craft["lon"]
        cot = adsbcot.functions.adsb_to_cot_xml(craft)
        assert cot is None


if __name__ == "__main__":
    unittest.main()
