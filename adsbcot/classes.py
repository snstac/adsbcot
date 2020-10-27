#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Class Definitions."""

import json
import logging
import os
import queue
import random
import threading
import time

import pycot
import requests

import adsbcot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class ADSBWorker(threading.Thread):
    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, msg_queue: queue.Queue, url: str, interval: int = None,
                 stale: int = None, api_key: str = None):
        self.msg_queue: queue.Queue = msg_queue
        self.url: str = url
        self.interval: int = int(interval or adsbcot.DEFAULT_INTERVAL)
        self.stale: int = stale
        self.api_key: str = api_key

        # Thread setup:
        threading.Thread.__init__(self)
        self.daemon = True
        self._stopper = threading.Event()

    def stop(self):
        """Stop the thread at the next opportunity."""
        self._logger.debug('Stopping ADSBWorker')
        self._stopper.set()

    def stopped(self):
        """Checks if the thread is stopped."""
        return self._stopper.isSet()

    def _put_queue(self, aircraft: list) -> None:
        if not aircraft:
            self._logger.warning('Empty aircraft list')
            return False

        i = 1
        for craft in aircraft:
            cot_event = adsbcot.adsb_to_cot(craft, stale=self.stale)
            if not cot_event:
                self._logger.debug(f'Empty CoT Event for craft={craft}')
                i += 1
                continue

            self._logger.debug(
                'Handling %s/%s ICAO24: %s Flight: %s ',
                i, len(aircraft), craft.get('hex'), craft.get('flight'))

            rendered_event = cot_event.render(
                encoding='UTF-8', standalone=True)

            if rendered_event:
                try:
                    self.msg_queue.put(rendered_event, True, 10)
                except queue.Full as exc:
                    self._logger.exception(exc)
                    self._logger.warning(
                        'Lost CoT Event (queue full): "%s"', rendered_event)
            i += 1

    def _get_dump1090_feed(self):
        response = requests.get(self.url)
        if response.ok:
            aircraft = response.json().get('aircraft')
            self._logger.debug('Retrieved %s aircraft', len(aircraft))
            self._put_queue(aircraft)

    def _get_adsbx_feed(self) -> None:
        headers = {'api-auth': self.api_key}
        response = requests.get(self.url, headers=headers)
        jresponse = json.loads(response.text)
        aircraft = jresponse.get('ac')
        self._logger.debug('Retrieved %s aircraft', len(aircraft))
        self._put_queue(aircraft)

    def run(self):
        """Runs this Thread, Reads from Pollers."""
        self._logger.info('Running ADSBWorker')

        while not self.stopped():
            if 'aircraft.json' in self.url:
                self._get_dump1090_feed()
            else:
                self._get_adsbx_feed()
            time.sleep(self.interval)
