#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Function Tests."""

import unittest

import adsbcot.functions

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


TEST_DUMP1090_FEED = {
    "now" : 1602849987.1,
    "messages" : 1799595081,
    "aircraft" : [
        {"hex":"a9ee47","flight":"N739UL  ","alt_baro":3700,"alt_geom":3750,"gs":79.5,"track":50.1,"geom_rate":512,"category":"A1","lat":37.836449,"lon":-122.030281,"nic":9,"rc":75,"seen_pos":1.0,"version":2,"nic_baro":0,"nac_p":10,"nac_v":2,"sil":3,"sil_type":"perhour","gva":2,"sda":2,"mlat":[],"tisb":[],"messages":34,"seen":0.2,"rssi":-15.8},
        {"hex":"3c4586","alt_baro":37000,"alt_geom":38650,"gs":487.6,"track":171.3,"baro_rate":0,"version":0,"nac_v":1,"mlat":[],"tisb":[],"messages":10,"seen":17.0,"rssi":-18.2},
        {"hex":"a18b41","alt_baro":39000,"squawk":"3514","nav_qnh":1013.6,"nav_altitude_mcp":39008,"nav_modes":["autopilot","vnav","tcas"],"lat":39.455023,"lon":-120.402344,"nic":8,"rc":186,"seen_pos":12.6,"version":0,"nic_baro":1,"nac_p":10,"sil":3,"sil_type":"unknown","mlat":[],"tisb":[],"messages":17,"seen":3.2,"rssi":-18.9},
        {"hex":"abd994","flight":"SWA1241 ","alt_baro":17650,"alt_geom":18650,"gs":353.4,"track":321.1,"baro_rate":-2112,"category":"A3","nav_qnh":1013.6,"nav_altitude_mcp":3392,"nav_heading":308.0,"version":0,"nic_baro":1,"nac_p":8,"nac_v":1,"sil":2,"sil_type":"unknown","mlat":[],"tisb":[],"messages":14,"seen":16.7,"rssi":-18.1},
    ]
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
        aircraft = TEST_DUMP1090_FEED['aircraft']
        craft = aircraft[0]
        cot_msg = adsbcot.functions.adsb_to_cot(craft)
        self.assertEqual(cot_msg.event_type, 'a-n-A-C-F')
        self.assertEqual(cot_msg.uid, 'ICAO24.a9ee47')


if __name__ == '__main__':
    unittest.main()
