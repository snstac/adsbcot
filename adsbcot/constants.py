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


if os.getenv("DEBUG"):
    LOG_LEVEL = logging.DEBUG
    LOG_FORMAT = logging.Formatter(
        (
            "%(asctime)s adsbcot %(levelname)s %(name)s.%(funcName)s:%(lineno)d "
            " - %(message)s"
        )
    )
    logging.debug("adsbcot Debugging Enabled via DEBUG Environment Variable.")
else:
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = logging.Formatter(("%(asctime)s adsbcot %(levelname)s - %(message)s"))

DEFAULT_POLL_INTERVAL: int = 30

DEFAULT_DUMP1090_TCP_RAW_PORT: int = 30002
DEFAULT_DUMP1090_TCP_BEAST_PORT: int = 30005
DEFAULT_DUMP1090_URL: str = (
    f"tcp+beast://piaware.local:{DEFAULT_DUMP1090_TCP_BEAST_PORT}"
)
