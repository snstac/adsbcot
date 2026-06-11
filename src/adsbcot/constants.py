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

"""ADSBCOT Constants."""

# Feed URL to use out of the box, in this case the JSON from the local filesystem.
DEFAULT_FEED_URL: str = "file:///run/dump1090-fa/aircraft.json"

# Default HTTP JSON feed polling interval, in seconds.
DEFAULT_POLL_INTERVAL: str = "3"

# Default non-HTTP TCP ports for raw & beast.
DEFAULT_TCP_RAW_PORT: int = 30003
DEFAULT_TCP_BEAST_PORT: int = 30005

DEFAULT_RAPIDAPI_HOST: str = "adsb-exchange1.p.rapidapi.com"

# Sensor keep-alive / heartbeat
DEFAULT_SENSOR_KEEPALIVE_PERIOD: int = 30
DEFAULT_SENSOR_LAT: float = 0.0
DEFAULT_SENSOR_LON: float = 0.0
DEFAULT_SENSOR_HAE: float = 0.0

import socket as _socket
DEFAULT_SENSOR_ID: str = f"adsbcot_{_socket.gethostname()}"
DEFAULT_SENSOR_COT_TYPE: str = "a-f-G-E-S-E"
DEFAULT_SENSOR_PAYLOAD_TYPE: str = "ADS-B-Receiver"
