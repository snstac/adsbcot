#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ADS-B Cursor-on-Target Gateway.

"""
ADS-B Cursor-on-Target Gateway.
~~~~


:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2020 Orion Labs, Inc.
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/adsbcot>

"""

from .constants import (LOG_FORMAT, LOG_LEVEL, DEFAULT_COT_PORT,  # NOQA
                        DEFAULT_INTERVAL)

from .functions import adsb_to_cot  # NOQA

from .classes import ADSBCoT  # NOQA

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'
