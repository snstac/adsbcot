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

"""ADSBCOT Constants."""

import logging
import os

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


# Dump1090 URL to use out of the box, in this case the HTTP JSON feed URL.
DEFAULT_DUMP1090_URL: str = "http://piaware.local:8080/data/aircraft.json"

# Default dump1090 HTTP JSON feed polling interval, in seconds.
DEFAULT_POLL_INTERVAL: str = "3"

# Default non-HTTP TCP ports for dump1090, raw & beast.
DEFAULT_DUMP1090_TCP_RAW_PORT: int = 30002
DEFAULT_DUMP1090_TCP_BEAST_PORT: int = 30005
