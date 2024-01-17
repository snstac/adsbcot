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

__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright Sensors & Signals LLC https://www.snstac.com"
__license__ = "Apache License, Version 2.0"


# Feed URL to use out of the box, in this case the JSON from the local filesystem.
DEFAULT_FEED_URL: str = "file:///run/dump1090-fa/aircraft.json"

# Default HTTP JSON feed polling interval, in seconds.
DEFAULT_POLL_INTERVAL: str = "3"

# Default non-HTTP TCP ports for raw & beast.
DEFAULT_TCP_RAW_PORT: int = 30003
DEFAULT_TCP_BEAST_PORT: int = 30005
