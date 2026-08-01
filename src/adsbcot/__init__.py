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

"""ADS-B to TAK Gateway."""

import os as _os


def _read_version() -> str:
    """Return the running version, for the runtime status surface.

    The VERSION file beside this module is checked FIRST, on purpose: it is the
    version of the code actually executing. importlib.metadata reports whatever
    is *installed*, which during development -- PYTHONPATH=src over an older
    system package -- is a different, older answer. A status surface that
    misreports which build is running is worse than one that reports nothing,
    so metadata is only the fallback for builds that ship no VERSION file.
    """
    try:
        with open(
            _os.path.join(_os.path.dirname(__file__), "VERSION"), encoding="utf-8"
        ) as version_fd:
            return version_fd.read().strip()
    except OSError:
        pass
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("adsbcot")
    except Exception:  # noqa: BLE001 -- a version string is never worth a crash
        return "unknown"


__version__: str = _read_version()

from .constants import (  # NOQA
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TCP_RAW_PORT,
    DEFAULT_TCP_BEAST_PORT,
    DEFAULT_FEED_URL,
    DEFAULT_RAPIDAPI_HOST,
    DEFAULT_SENSOR_KEEPALIVE_PERIOD,
    DEFAULT_SENSOR_LAT,
    DEFAULT_SENSOR_LON,
    DEFAULT_SENSOR_HAE,
    DEFAULT_SENSOR_ID,
    DEFAULT_SENSOR_COT_TYPE,
    DEFAULT_SENSOR_PAYLOAD_TYPE,
)

from .functions import adsb_to_cot, create_tasks, gen_sensor_cot  # NOQA

from .classes import ADSBWorker, ADSBNetReceiver, ADSBNetWorker, SensorWorker  # NOQA
