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

"""ADS-B to TAK Gateway.

:source: <https://github.com/snstac/adsbcot>
"""

__version__ = "7.0.1"
__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright Sensors & Signals LLC https://www.snstac.com"
__license__ = "Apache License, Version 2.0"

# Python 3.6 test/build work-around:
try:
    from .constants import (  # NOQA
        DEFAULT_POLL_INTERVAL,
        DEFAULT_TCP_RAW_PORT,
        DEFAULT_TCP_BEAST_PORT,
        DEFAULT_FEED_URL,
    )

    from .functions import adsb_to_cot, create_tasks  # NOQA

    from .classes import ADSBWorker, ADSBNetReceiver, ADSBNetWorker  # NOQA
except ImportError as exc:
    import warnings

    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError - Python 3.6 compat work-around.")
