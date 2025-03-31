#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com/
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


"""adsbcot Function Tests."""

import asyncio
import csv
import io
import urllib
import xml.etree.ElementTree as ET

import pytest

import adsbcot
import adsbcot.functions

# Sample JSON data:
#
# {
#  'Icao_addr': 11160165,
#  'Reg': 'N762QS',
#  'Tail': 'N762QS',
#  'Squawk': 0,
#  'Lat': 37.89692,
#  'Lng': -122.74547,
#  'Addr_type': 0,
#  'Age': 28.29,
#  'AgeLastAlt': 1.33,
#  'Alt': 21850,
#  'AltIsGNSS': False,
#  'Bearing': 0,
#  'BearingDist_valid': False,
#  'Distance': 0,
#  'Emitter_category': 0,
#  'ExtrapolatedPosition': False,
#  'GnssDiffFromBaroAlt': -275,
#  'LastSent': '0001-01-01T00:39:16.44Z',
#  'Last_GnssDiff': '0001-01-01T00:39:53.84Z',
#  'Last_GnssDiffAlt': 21775,
#  'Last_alt': '0001-01-01T00:39:54.77Z',
#  'Last_seen': '0001-01-01T00:39:54.77Z',
#  'Last_source': 1,
#  'Last_speed': '0001-01-01T00:39:53.84Z',
#  'NACp': 10,
#  'NIC': 8,
#  'OnGround': False,
#  'Position_valid': True,
#  'PriorityStatus': 0,
#  'SignalLevel': -28.21023052706831,
#  'Speed': 340,
#  'Speed_valid': True,
#  'TargetType': 1,
#  'Timestamp': '2020-11-06T19:58:06.234Z',
#  'Track': 249,
#  'Vvel': 3392
#  }
#

#
# "Last_seen":"0001-01-01T00:43:19.61Z"  (ws://192.168.10.1/traffic)   0001-01-01 is day zero,
# +
# "GPSTime":"2020-05-12T08:27:10Z" (http://192.168.10.1/getSituation)
# -
# ("Uptime":2610230,ms)"UptimeClock":"0001-01-01T00:43:30.23Z" (http://192.168.10.1/getStatus)
# = Timestamp of traffic "event"
#

#
# This is an illuminated/commented version of the traffic output from StratuX:
# type TrafficInfo struct {
# Icao_addr          uint32   // decimal version of (ICAO HEX or ICAO OCTAL)
# Reg                string   // Registration. Calculated from Icao_addr for civil aircraft of US registry.
# Tail               string   // Callsign. Transmitted by aircraft. 8 Characters max including spaces
# Emitter_category   uint8    // Formatted using GDL90 standard 3.5.1.10 Table 11, e.g. in a Mode ES report, A7 becomes 0x07, B0 becomes 0x08, etc.
# OnGround           bool     // Air-ground status. On-ground is "true".
# Addr_type          uint8    // UAT address qualifier. Used by GDL90 format, so translations for ES TIS-B/ADS-R are needed. 3.5.1.2 Target Identity
# (GDL90 ICD)
# TargetType         uint8    // types decribed in const above https://github.com/cyoung/stratux/blob/master/main/traffic.go#L66
# SignalLevel        float64  // Signal level, dB RSSI.
# Squawk             int      // Squawk code
# Position_valid     bool     // false = MODE-S message without location data
# Lat                float32  // decimal degrees, north positive
# Lng                float32  // decimal degrees, east positive
# Alt                int32    // Pressure altitude, feet
# GnssDiffFromBaroAlt int32    // GNSS altitude above WGS84 datum. Reported in TC 20-22 messages (negative = below BaroAlt, smaller magnitude)
# AltIsGNSS          bool     // Pressure alt = 0; GNSS alt = 1
# NIC                int      // Navigation Integrity Category.
# NACp               int      // Navigation Accuracy Category for Position.
# Track              uint16   // degrees true
# Speed              uint16   // knots
# Speed_valid        bool     // set when speed report received.
# Vvel               int16    // feet per minute
# Timestamp          time.Time // timestamp of traffic message, UTC
# PriorityStatus     uint8    // Emergency or priority code as defined in GDL90 spec, DO-260B (Type 28 msg) and DO-282B
# // Parameters starting at 'Age' are calculated from last message receipt on each call of sendTrafficUpdates().
# // Mode S transmits position and track in separate messages, and altitude can also be
# // received from interrogations.
# Age                 float64  // Age of last valid position fix, seconds ago.
# AgeLastAlt          float64  // Age of last altitude message, seconds ago.
# Last_seen           time.Time // Time of last position update (stratuxClock). Used for timing out expired data.
# Last_alt            time.Time // Time of last altitude update (stratuxClock).
# Last_GnssDiff       time.Time // Time of last GnssDiffFromBaroAlt update (stratuxClock).
# Last_GnssDiffAlt    int32    // Altitude at last GnssDiffFromBaroAlt update.
# Last_speed          time.Time // Time of last velocity and track update (stratuxClock).
# Last_source         uint8    // Last frequency on which this target was received.
# ExtrapolatedPosition bool     //TODO: True if Stratux is "coasting" the target from last known position.
# BearingDist_valid   bool     // set when bearing and distance information is valid
# Bearing             float64  // Bearing in degrees true to traffic from ownship, if it can be calculated. Units: degrees.
# Distance            float64  // Distance to traffic from ownship, if it can be calculated. Units: meters.
# //FIXME: Rename variables for consistency, especially "Last_".
#


@pytest.fixture
def sample_craft():
    return {
        "Icao_addr": 10698088,
        "Reg": "N308DU",
        "Tail": "DAL1352",
        "Emitter_category": 3,
        "OnGround": False,
        "Addr_type": 0,
        "TargetType": 1,
        "SignalLevel": -35.5129368009492,
        "Squawk": 3105,
        "Position_valid": True,
        "Lat": 37.46306,
        "Lng": -122.264626,
        "Alt": 7325,
        "GnssDiffFromBaroAlt": 25,
        "AltIsGNSS": False,
        "NIC": 8,
        "NACp": 10,
        "Track": 135,
        "Speed": 262,
        "Speed_valid": True,
        "Vvel": -1600,
        "Timestamp": "2021-05-19T23:13:18.484Z",
        "PriorityStatus": 0,
        "Age": 29.85,
        "AgeLastAlt": 29.83,
        "Last_seen": "0001-01-01T16:43:24.75Z",
        "Last_alt": "0001-01-01T16:43:24.77Z",
        "Last_GnssDiff": "0001-01-01T16:43:24.54Z",
        "Last_GnssDiffAlt": 7700,
        "Last_speed": "0001-01-01T16:43:24.54Z",
        "Last_source": 1,
        "ExtrapolatedPosition": False,
        "BearingDist_valid": True,
        "Bearing": 148.05441175901748,
        "Distance": 38889.68863349082,
        "LastSent": "0001-01-01T16:43:22.85Z",
    }


@pytest.fixture
def sample_craft25():
    return {
        "Icao_addr": 10561017,
        "Reg": "N173SY",
        "Tail": "N173SY",
        "Emitter_category": 0,
        "OnGround": False,
        "Addr_type": 0,
        "TargetType": 1,
        "SignalLevel": -19.873314661036694,
        "Squawk": 0,
        "Position_valid": True,
        "Lat": 37.732635,
        "Lng": -122.496124,
        "Alt": 10925,
        "GnssDiffFromBaroAlt": 225,
        "AltIsGNSS": False,
        "NIC": 8,
        "NACp": 10,
        "Track": 140,
        "TurnRate": 0,
        "Speed": 275,
        "Speed_valid": True,
        "Vvel": -64,
        "Timestamp": "2025-03-26T17:12:23.235Z",
        "PriorityStatus": 0,
        "Age": 0.65,
        "AgeLastAlt": 0.65,
        "Last_seen": "0001-01-01T01:42:59.26Z",
        "Last_alt": "0001-01-01T01:42:59.26Z",
        "Last_GnssDiff": "0001-01-01T01:42:59.26Z",
        "Last_GnssDiffAlt": 10925,
        "Last_speed": "0001-01-01T01:42:51.51Z",
        "Last_source": 1,
        "ExtrapolatedPosition": False,
        "Last_extrapolation": "0001-01-01T00:00:00Z",
        "AgeExtrapolation": 6178.81,
        "Lat_fix": 0,
        "Lng_fix": 0,
        "Alt_fix": 0,
        "BearingDist_valid": True,
        "Bearing": 177.36308118139144,
        "Distance": 3047.9584204684284,
        "DistanceEstimated": 7979.412664109308,
        "DistanceEstimatedLastTs": "2025-03-26T17:12:23.235Z",
        "ReceivedMsgs": 41,
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
FOOD,EL FAROLITO,DAL1352,TACO_02,FIXED WING,,,a-f-A-T-A-C-O,FIXED WING,,
"""
    csv_fd = io.StringIO(sample_csv)
    all_rows = []
    reader = csv.DictReader(csv_fd)
    for row in reader:
        all_rows.append(row)
    print(all_rows)
    return all_rows


def test_adsb_to_cot(sample_craft):
    print(sample_craft)
    cot = adsbcot.functions.adsb_to_cot_xml(sample_craft)
    print(ET.tostring(cot))

    assert isinstance(cot, ET.Element)
    assert cot.tag == "event"
    assert cot.attrib["version"] == "2.0"
    assert cot.attrib["type"] == "a-n-A-C"
    assert cot.attrib["uid"] == "ICAO-A33D68"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.46306"
    assert point[0].attrib["lon"] == "-122.264626"
    assert point[0].attrib["hae"] == "2232.6600000000003"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "135"
    assert track[0].attrib["speed"] == "134.78432800000002"


def test_adsb_to_cot_with_known_craft(sample_craft, sample_known_craft):
    known_craft_key = "REG"
    filter_key = sample_craft["Tail"].strip().upper()

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
    assert cot.attrib["uid"] == "ICAO-A33D68"

    point = cot.findall("point")
    assert point[0].tag == "point"
    assert point[0].attrib["lat"] == "37.46306"
    assert point[0].attrib["lon"] == "-122.264626"
    assert point[0].attrib["hae"] == "2232.6600000000003"

    detail = cot.findall("detail")
    assert detail[0].tag == "detail"

    track = detail[0].findall("track")
    assert track[0].attrib["course"] == "135"
    assert track[0].attrib["speed"] == "134.78432800000002"


def test_negative_adsb_to_cot():
    sample_craft = {"taco": "burrito"}
    cot = adsbcot.adsb_to_cot(sample_craft)
    assert cot == None
