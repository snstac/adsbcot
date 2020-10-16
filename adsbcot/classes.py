#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Class Definitions."""

import logging
import os
import threading
import random
import time

import pycot
import requests

import adsbcot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class ADSBCoT(threading.Thread):

    """ADS-B Cursor-on-Target Threaded Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, dump1090_url: str, cot_host: str,
                 interval: int = None) -> None:
        self.dump1090_url: str = dump1090_url
        self.cot_host: str = cot_host
        self.interval: int = interval or adsbcot.DEFAULT_INTERVAL

        self.net_client = pycot.NetworkClient(self.cot_host)

        # Thread setup:
        threading.Thread.__init__(self)
        self._stopped = False

    def stop(self):
        """Stop the thread at the next opportunity."""
        self._stopped = True
        return self._stopped

    def send_cot(self, craft: dict) -> bool:
        """Sends an ADS-B to a Cursor-on-Target Host."""
        self._logger.debug(
            'Handling ICAO24: %s Flight: %s ',
            craft.get('hex'), craft.get('flight'))

        cot_event = adsbcot.adsb_to_cot(craft)
        if cot_event is None:
            return False

        rendered_event = cot_event.render(encoding='UTF-8', standalone=True)

        self._logger.debug(
            'Sending CoT to %s : "%s"', self.cot_host, rendered_event)

        return self.net_client.sendall(rendered_event)

    def run(self):
        """Runs this Thread, reads ADS-B & outputs CoT."""
        self._logger.info('Running ADSBCoT Thread...')

        while 1:
            response = requests.get(self.dump1090_url)
            if response.ok:
                aircraft = response.json().get('aircraft')
                self._logger.debug('Retrieved %s aircraft', len(aircraft))
                for craft in aircraft:
                    self.send_cot(craft)
                    if not os.environ.get('NO_RANDOM_SLEEP'):
                        time.sleep(random.random())  # backoff for server
            time.sleep(self.interval)
